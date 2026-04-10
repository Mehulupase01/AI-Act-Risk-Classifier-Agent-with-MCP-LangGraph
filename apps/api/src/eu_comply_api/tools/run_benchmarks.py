from __future__ import annotations

import argparse
import asyncio
import json

from eu_comply_api.services.benchmark_service import BenchmarkService


async def run_benchmarks() -> int:
    summary = await BenchmarkService().run()
    print(json.dumps(summary.model_dump(mode="json"), indent=2))
    return 0 if not summary.failures else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EU-Comply benchmark scenarios.")
    parser.parse_args()
    raise SystemExit(asyncio.run(run_benchmarks()))


if __name__ == "__main__":
    main()
