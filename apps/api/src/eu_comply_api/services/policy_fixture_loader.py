from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from anyio import Path as AsyncPath
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.db.models import NormFragmentRecord, PolicySnapshotRecord, PolicySourceRecord

DEFAULT_POLICY_FIXTURE_PATH = (
    Path(__file__).resolve().parents[5] / "fixtures" / "policies" / "eu_ai_act_snapshot.json"
)


class PolicyFixtureLoader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def seed_default_fixture(self, fixture_path: str | None = None) -> bool:
        path_value = Path(fixture_path) if fixture_path else DEFAULT_POLICY_FIXTURE_PATH
        path = AsyncPath(path_value)
        if not await path.exists():
            return False

        payload = json.loads(await path.read_text(encoding="utf-8"))
        await self.upsert_payload(payload)
        return True

    async def upsert_payload(self, payload: dict[str, Any]) -> None:
        for source in payload.get("sources", []):
            existing_source = await self._session.scalar(
                select(PolicySourceRecord).where(PolicySourceRecord.slug == source["slug"])
            )
            if existing_source is None:
                self._session.add(
                    PolicySourceRecord(
                        slug=source["slug"],
                        title=source["title"],
                        source_type=source["source_type"],
                        authority=source["authority"],
                        url=source["url"],
                        status=source["status"],
                    )
                )
        await self._session.flush()

        source_records = list(
            (
                await self._session.scalars(
                    select(PolicySourceRecord).where(
                        PolicySourceRecord.slug.in_(
                            [source["slug"] for source in payload.get("sources", [])]
                        )
                    )
                )
            ).all()
        )
        source_by_slug = {source.slug: source for source in source_records}

        snapshot_payload = payload["snapshot"]
        snapshot = await self._session.scalar(
            select(PolicySnapshotRecord).where(
                PolicySnapshotRecord.slug == snapshot_payload["slug"]
            )
        )
        if snapshot is None:
            snapshot = PolicySnapshotRecord(
                slug=snapshot_payload["slug"],
                title=snapshot_payload["title"],
                jurisdiction=snapshot_payload["jurisdiction"],
                effective_from=snapshot_payload["effective_from"],
                description=snapshot_payload["description"],
                source_ids=[source["slug"] for source in payload.get("sources", [])],
            )
            self._session.add(snapshot)
            await self._session.flush()

        for fragment in payload.get("fragments", []):
            existing_fragment = await self._session.scalar(
                select(NormFragmentRecord).where(
                    NormFragmentRecord.snapshot_id == snapshot.id,
                    NormFragmentRecord.fragment_type == fragment["fragment_type"],
                    NormFragmentRecord.citation == fragment["citation"],
                )
            )
            if existing_fragment is not None:
                continue

            source = source_by_slug.get(fragment["source_slug"])
            if source is None:
                raise ValueError(
                    f"Unknown policy source slug '{fragment['source_slug']}' in policy fixture."
                )

            self._session.add(
                NormFragmentRecord(
                    snapshot_id=snapshot.id,
                    source_id=source.id,
                    fragment_type=fragment["fragment_type"],
                    citation=fragment["citation"],
                    heading=fragment["heading"],
                    body=fragment["body"],
                    actor_scope=fragment.get("actor_scope", []),
                    tags=fragment.get("tags", []),
                    order_index=fragment.get("order_index", 0),
                    metadata_json=fragment.get("metadata_json", {}),
                )
            )
