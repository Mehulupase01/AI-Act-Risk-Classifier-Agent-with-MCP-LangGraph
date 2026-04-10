from __future__ import annotations

from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eu_comply_api.config import Settings
from eu_comply_api.db.models import (
    ArtifactChunkRecord,
    ArtifactRecord,
    CaseRecord,
    ExtractedFactRecord,
)
from eu_comply_api.domain.models import (
    ArtifactChunkSummary,
    ArtifactDetail,
    ArtifactProcessResponse,
    ArtifactStatus,
    ArtifactSummary,
    ExtractedFactStatus,
    ExtractedFactSummary,
)
from eu_comply_api.services.artifact_storage_service import ArtifactStorageService
from eu_comply_api.services.document_intelligence_service import DocumentIntelligenceService


class ArtifactService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._storage = ArtifactStorageService(settings)
        self._document_intelligence = DocumentIntelligenceService(settings)

    async def list_artifacts(self, organization_id: UUID, case_id: UUID) -> list[ArtifactSummary]:
        await self._get_case(organization_id, case_id)
        artifacts = list(
            (
                await self._session.scalars(
                    select(ArtifactRecord)
                    .where(ArtifactRecord.case_id == case_id)
                    .order_by(ArtifactRecord.created_at.desc())
                )
            ).all()
        )
        return [self._to_artifact_summary(artifact) for artifact in artifacts]

    async def upload_artifact(
        self,
        organization_id: UUID,
        case_id: UUID,
        file: UploadFile,
    ) -> ArtifactDetail:
        case = await self._get_case(organization_id, case_id)
        payload = await file.read()
        relative_path, sha256 = await self._storage.write_artifact(
            organization_id=organization_id,
            case_id=case_id,
            filename=file.filename or "artifact.bin",
            payload=payload,
        )
        artifact = ArtifactRecord(
            case_id=case.id,
            filename=file.filename or "artifact.bin",
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(payload),
            sha256=sha256,
            storage_path=relative_path,
            status=ArtifactStatus.UPLOADED.value,
        )
        self._session.add(artifact)
        await self._session.commit()
        return await self.get_artifact(organization_id, case_id, artifact.id)

    async def get_artifact(
        self,
        organization_id: UUID,
        case_id: UUID,
        artifact_id: UUID,
    ) -> ArtifactDetail:
        await self._get_case(organization_id, case_id)
        artifact = await self._session.scalar(
            select(ArtifactRecord)
            .execution_options(populate_existing=True)
            .options(
                selectinload(ArtifactRecord.chunks),
                selectinload(ArtifactRecord.extracted_facts),
            )
            .where(
                ArtifactRecord.case_id == case_id,
                ArtifactRecord.id == artifact_id,
            )
        )
        if artifact is None:
            raise ValueError(f"Artifact '{artifact_id}' was not found.")
        return self._to_artifact_detail(artifact)

    async def process_artifact(
        self,
        organization_id: UUID,
        case_id: UUID,
        artifact_id: UUID,
    ) -> ArtifactProcessResponse:
        await self._get_case(organization_id, case_id)
        artifact = await self._session.scalar(
            select(ArtifactRecord)
            .execution_options(populate_existing=True)
            .options(
                selectinload(ArtifactRecord.chunks),
                selectinload(ArtifactRecord.extracted_facts),
            )
            .where(
                ArtifactRecord.case_id == case_id,
                ArtifactRecord.id == artifact_id,
            )
        )
        if artifact is None:
            raise ValueError(f"Artifact '{artifact_id}' was not found.")

        payload = await self._storage.read_artifact(artifact.storage_path)

        await self._session.execute(
            delete(ArtifactChunkRecord).where(ArtifactChunkRecord.artifact_id == artifact.id)
        )
        await self._session.execute(
            delete(ExtractedFactRecord).where(ExtractedFactRecord.artifact_id == artifact.id)
        )

        try:
            parsed = self._document_intelligence.parse_document(
                artifact.filename,
                artifact.content_type,
                payload,
            )
            chunks = self._document_intelligence.chunk_text(parsed.text)
            artifact.parser_name = parsed.parser_name
            artifact.processing_error = None
            artifact.status = ArtifactStatus.PROCESSED.value

            chunk_records: list[ArtifactChunkRecord] = []
            for chunk in chunks:
                record = ArtifactChunkRecord(
                    artifact_id=artifact.id,
                    chunk_index=chunk.chunk_index,
                    text_content=chunk.text_content,
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    metadata_json=chunk.metadata_json,
                )
                self._session.add(record)
                chunk_records.append(record)
            await self._session.flush()

            candidates = self._document_intelligence.extract_fact_candidates(chunks)
            fact_records: list[ExtractedFactRecord] = []
            for candidate in candidates:
                fact_records.append(
                    ExtractedFactRecord(
                        case_id=case_id,
                        artifact_id=artifact.id,
                        field_path=candidate.field_path,
                        value_json={"value": candidate.value},
                        confidence=candidate.confidence,
                        extraction_method=candidate.extraction_method,
                        status=ExtractedFactStatus.CANDIDATE.value,
                        rationale=candidate.rationale,
                        source_chunk_indexes=candidate.source_chunk_indexes,
                    )
                )
            for record in fact_records:
                self._session.add(record)
            await self._session.flush()
            await self._apply_conflict_status(case_id)
        except Exception as exc:
            artifact.status = ArtifactStatus.FAILED.value
            artifact.processing_error = str(exc)

        await self._session.commit()
        detail = await self.get_artifact(organization_id, case_id, artifact.id)
        conflict_count = sum(
            1 for fact in detail.extracted_facts if fact.status == ExtractedFactStatus.CONFLICT
        )
        return ArtifactProcessResponse(
            artifact=detail,
            chunk_count=len(detail.chunks),
            fact_count=len(detail.extracted_facts),
            conflict_count=conflict_count,
        )

    async def _get_case(self, organization_id: UUID, case_id: UUID) -> CaseRecord:
        case = await self._session.scalar(
            select(CaseRecord).where(
                CaseRecord.organization_id == organization_id,
                CaseRecord.id == case_id,
            )
        )
        if case is None:
            raise ValueError(f"Case '{case_id}' was not found.")
        return case

    async def _apply_conflict_status(self, case_id: UUID) -> None:
        facts = list(
            (
                await self._session.scalars(
                    select(ExtractedFactRecord).where(ExtractedFactRecord.case_id == case_id)
                )
            ).all()
        )
        grouped: dict[str, set[str]] = {}
        for fact in facts:
            grouped.setdefault(fact.field_path, set()).add(str(fact.value_json))

        for fact in facts:
            has_conflict = len(grouped[fact.field_path]) > 1
            fact.status = (
                ExtractedFactStatus.CONFLICT.value
                if has_conflict
                else ExtractedFactStatus.CANDIDATE.value
            )

    def _to_artifact_summary(self, artifact: ArtifactRecord) -> ArtifactSummary:
        return ArtifactSummary(
            id=artifact.id,
            case_id=artifact.case_id,
            filename=artifact.filename,
            content_type=artifact.content_type,
            size_bytes=artifact.size_bytes,
            sha256=artifact.sha256,
            status=ArtifactStatus(artifact.status),
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
        )

    def _to_artifact_detail(self, artifact: ArtifactRecord) -> ArtifactDetail:
        return ArtifactDetail(
            **self._to_artifact_summary(artifact).model_dump(),
            parser_name=artifact.parser_name,
            processing_error=artifact.processing_error,
            chunks=[
                ArtifactChunkSummary(
                    id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    text_preview=chunk.text_content[:180],
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                )
                for chunk in artifact.chunks
            ],
            extracted_facts=[
                ExtractedFactSummary(
                    id=fact.id,
                    field_path=fact.field_path,
                    value=fact.value_json.get("value"),
                    confidence=fact.confidence,
                    extraction_method=fact.extraction_method,
                    status=ExtractedFactStatus(fact.status),
                    rationale=fact.rationale,
                )
                for fact in artifact.extracted_facts
            ],
        )
