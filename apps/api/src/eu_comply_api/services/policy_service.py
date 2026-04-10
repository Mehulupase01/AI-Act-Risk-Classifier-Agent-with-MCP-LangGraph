from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eu_comply_api.db.models import NormFragmentRecord, PolicySnapshotRecord, PolicySourceRecord
from eu_comply_api.domain.models import (
    NormFragmentSummary,
    PolicySnapshotDetail,
    PolicySnapshotSummary,
    PolicySourceSummary,
)


class PolicyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_sources(self) -> list[PolicySourceSummary]:
        source_records = list(
            (
                await self._session.scalars(
                    select(PolicySourceRecord).order_by(PolicySourceRecord.title.asc())
                )
            ).all()
        )
        return [self._to_source_summary(source) for source in source_records]

    async def list_snapshots(self) -> list[PolicySnapshotSummary]:
        snapshots = list(
            (
                await self._session.scalars(
                    select(PolicySnapshotRecord).order_by(PolicySnapshotRecord.effective_from.desc())
                )
            ).all()
        )
        if not snapshots:
            return []

        source_by_slug = await self._load_source_map()
        return [self._to_snapshot_summary(snapshot, source_by_slug) for snapshot in snapshots]

    async def get_snapshot(self, snapshot_slug: str) -> PolicySnapshotDetail | None:
        snapshot = await self._session.scalar(
            select(PolicySnapshotRecord)
            .options(
                selectinload(PolicySnapshotRecord.fragments).selectinload(NormFragmentRecord.source),
            )
            .where(PolicySnapshotRecord.slug == snapshot_slug)
        )
        if snapshot is None:
            return None

        source_by_slug = await self._load_source_map()
        summary = self._to_snapshot_summary(snapshot, source_by_slug)
        fragments = [
            NormFragmentSummary(
                id=fragment.id,
                fragment_type=fragment.fragment_type,
                citation=fragment.citation,
                heading=fragment.heading,
                body=fragment.body,
                actor_scope=fragment.actor_scope,
                tags=fragment.tags,
                order_index=fragment.order_index,
                source_slug=fragment.source.slug,
                source_title=fragment.source.title,
            )
            for fragment in snapshot.fragments
        ]
        return PolicySnapshotDetail(**summary.model_dump(), fragments=fragments)

    async def _load_source_map(self) -> dict[str, PolicySourceRecord]:
        source_records = list((await self._session.scalars(select(PolicySourceRecord))).all())
        return {source.slug: source for source in source_records}

    def _to_source_summary(self, source: PolicySourceRecord) -> PolicySourceSummary:
        return PolicySourceSummary(
            id=source.id,
            slug=source.slug,
            title=source.title,
            source_type=source.source_type,
            authority=source.authority,
            url=source.url,
            status=source.status,
        )

    def _to_snapshot_summary(
        self,
        snapshot: PolicySnapshotRecord,
        source_by_slug: dict[str, PolicySourceRecord],
    ) -> PolicySnapshotSummary:
        sources = [
            self._to_source_summary(source_by_slug[source_slug])
            for source_slug in snapshot.source_ids
            if source_slug in source_by_slug
        ]
        return PolicySnapshotSummary(
            id=snapshot.id,
            slug=snapshot.slug,
            title=snapshot.title,
            jurisdiction=snapshot.jurisdiction,
            effective_from=datetime.fromisoformat(snapshot.effective_from),
            description=snapshot.description,
            sources=sources,
        )
