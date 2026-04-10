from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from anyio import Path as AsyncPath

from eu_comply_api.domain.models import (
    RuleCondition,
    RuleDefinition,
    RuleEvaluationResult,
    RuleHit,
    RuleOperator,
    RulePackDetail,
    RulePackSummary,
)

DEFAULT_RULE_PACK_DIR = Path(__file__).resolve().parents[5] / "fixtures" / "rule_packs"


class RulePackService:
    def __init__(self, rule_pack_dir: Path | None = None) -> None:
        self._rule_pack_dir = rule_pack_dir or DEFAULT_RULE_PACK_DIR

    async def list_rule_packs(self) -> list[RulePackSummary]:
        packs = await self._load_all_rule_packs()
        return [
            RulePackSummary(
                pack_id=pack.pack_id,
                title=pack.title,
                version=pack.version,
                snapshot_slug=pack.snapshot_slug,
                description=pack.description,
                rule_count=len(pack.rules),
            )
            for pack in packs
        ]

    async def get_rule_pack(self, pack_id: str) -> RulePackDetail | None:
        packs = await self._load_all_rule_packs()
        for pack in packs:
            if pack.pack_id == pack_id:
                return pack
        return None

    async def evaluate(self, pack_id: str, facts: dict[str, Any]) -> RuleEvaluationResult:
        pack = await self.get_rule_pack(pack_id)
        if pack is None:
            raise ValueError(f"Rule pack '{pack_id}' was not found.")

        hits = [
            RuleHit(
                rule_id=rule.rule_id,
                title=rule.title,
                outcome=rule.outcome,
                priority=rule.priority,
                citation_refs=rule.citation_refs,
                obligation_tags=rule.obligation_tags,
            )
            for rule in pack.rules
            if self._rule_matches(rule, facts)
        ]
        hits.sort(key=lambda hit: hit.priority, reverse=True)
        primary_outcome = hits[0].outcome if hits else None
        return RuleEvaluationResult(
            pack_id=pack.pack_id,
            primary_outcome=primary_outcome,
            hits=hits,
        )

    async def _load_all_rule_packs(self) -> list[RulePackDetail]:
        path = AsyncPath(self._rule_pack_dir)
        if not await path.exists():
            return []

        files: list[AsyncPath] = []
        async for file_path in path.iterdir():
            if file_path.suffix == ".json":
                files.append(file_path)
        files.sort(key=lambda item: item.name)
        packs: list[RulePackDetail] = []
        for file_path in files:
            raw = json.loads(await file_path.read_text(encoding="utf-8"))
            packs.append(self._parse_rule_pack(raw))
        return packs

    def _parse_rule_pack(self, payload: dict[str, Any]) -> RulePackDetail:
        metadata = payload["pack"]
        rules = [RuleDefinition.model_validate(rule) for rule in payload.get("rules", [])]
        return RulePackDetail(
            pack_id=metadata["pack_id"],
            title=metadata["title"],
            version=metadata["version"],
            snapshot_slug=metadata["snapshot_slug"],
            description=metadata["description"],
            rule_count=len(rules),
            rules=rules,
        )

    def _rule_matches(self, rule: RuleDefinition, facts: dict[str, Any]) -> bool:
        return all(self._condition_matches(condition, facts) for condition in rule.conditions)

    def _condition_matches(self, condition: RuleCondition, facts: dict[str, Any]) -> bool:
        value = self._resolve_field(facts, condition.field_path)

        if condition.operator == RuleOperator.EXISTS:
            return value is not None
        if condition.operator == RuleOperator.IS_TRUE:
            return value is True
        if condition.operator == RuleOperator.IS_FALSE:
            return value is False
        if condition.operator == RuleOperator.EQUALS:
            return value == condition.value
        if condition.operator == RuleOperator.NOT_EQUALS:
            return value != condition.value
        if condition.operator == RuleOperator.IN:
            expected = condition.value if isinstance(condition.value, list) else []
            return value in expected
        if condition.operator == RuleOperator.CONTAINS_ANY:
            if not isinstance(value, list):
                return False
            expected = condition.value if isinstance(condition.value, list) else []
            return any(item in value for item in expected)

        raise ValueError(f"Unsupported operator '{condition.operator}'.")

    def _resolve_field(self, facts: dict[str, Any], field_path: str) -> Any:
        current: Any = facts
        for segment in field_path.split("."):
            if not isinstance(current, dict) or segment not in current:
                return None
            current = current[segment]
        return current
