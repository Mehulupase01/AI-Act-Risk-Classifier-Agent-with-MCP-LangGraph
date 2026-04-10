from __future__ import annotations

import json
from pathlib import Path

from anyio import Path as AsyncPath

from eu_comply_api.domain.models import (
    AssessmentOutcome,
    BenchmarkRunSummary,
    BenchmarkScenario,
    BenchmarkScenarioResult,
)
from eu_comply_api.services.rule_pack_service import RulePackService

DEFAULT_BENCHMARK_FIXTURE = (
    Path(__file__).resolve().parents[5] / "packages" / "evaluation" / "golden_cases.json"
)


class BenchmarkService:
    def __init__(self, fixture_path: Path | None = None) -> None:
        self._fixture_path = fixture_path or DEFAULT_BENCHMARK_FIXTURE
        self._rule_pack_service = RulePackService()

    async def load_scenarios(self) -> list[BenchmarkScenario]:
        fixture = AsyncPath(self._fixture_path)
        if not await fixture.exists():
            return []
        payload = json.loads(await fixture.read_text(encoding="utf-8"))
        return [BenchmarkScenario.model_validate(item) for item in payload.get("cases", [])]

    async def run(self) -> BenchmarkRunSummary:
        scenarios = await self.load_scenarios()
        results: list[BenchmarkScenarioResult] = []
        for scenario in scenarios:
            evaluation = await self._rule_pack_service.evaluate(
                scenario.pack_id,
                scenario.facts,
            )
            actual_outcome = evaluation.primary_outcome or AssessmentOutcome.MINIMAL_RISK
            results.append(
                BenchmarkScenarioResult(
                    scenario_id=scenario.scenario_id,
                    expected_outcome=scenario.expected_outcome,
                    actual_outcome=actual_outcome,
                    passed=actual_outcome == scenario.expected_outcome,
                    matched_rule_ids=[hit.rule_id for hit in evaluation.hits],
                )
            )

        total_cases = len(results)
        passed_cases = sum(1 for result in results if result.passed)
        accuracy = passed_cases / total_cases if total_cases else 0.0
        return BenchmarkRunSummary(
            total_cases=total_cases,
            passed_cases=passed_cases,
            accuracy=accuracy,
            failures=[result for result in results if not result.passed],
        )
