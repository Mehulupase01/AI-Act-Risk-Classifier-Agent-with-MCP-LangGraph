import pytest

from eu_comply_api.services.benchmark_service import BenchmarkService


@pytest.mark.anyio
async def test_benchmark_fixture_runs_cleanly() -> None:
    summary = await BenchmarkService().run()

    assert summary.total_cases >= 5
    assert summary.passed_cases == summary.total_cases
    assert summary.accuracy == 1.0
    assert summary.failures == []
