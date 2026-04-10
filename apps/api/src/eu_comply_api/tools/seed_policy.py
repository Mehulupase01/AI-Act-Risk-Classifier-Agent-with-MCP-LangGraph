from __future__ import annotations

import argparse
import asyncio

from eu_comply_api.config import get_settings
from eu_comply_api.db.session import get_session_factory
from eu_comply_api.services.policy_fixture_loader import PolicyFixtureLoader


async def seed_policy(fixture_path: str | None) -> None:
    settings = get_settings()
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        loader = PolicyFixtureLoader(session)
        seeded = await loader.seed_default_fixture(fixture_path or settings.policy_fixture_path)
        await session.commit()

    if seeded:
        print("Policy fixture synchronized successfully.")
    else:
        print("Policy fixture path was not found; no policy data was synchronized.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed or refresh policy fixture data.")
    parser.add_argument(
        "--fixture-path",
        dest="fixture_path",
        default=None,
        help="Optional absolute or relative path to a policy fixture JSON file.",
    )
    args = parser.parse_args()
    asyncio.run(seed_policy(args.fixture_path))


if __name__ == "__main__":
    main()
