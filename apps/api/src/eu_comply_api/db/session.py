import asyncio
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from eu_comply_api.config import Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def reset_session_state() -> None:
    global _engine, _session_factory
    engine = _engine
    _engine = None
    _session_factory = None
    if engine is not None:
        try:
            asyncio.run(engine.dispose())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(engine.dispose())
            finally:
                loop.close()


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    global _engine
    if _engine is None:
        config = settings or get_settings()
        _engine = create_async_engine(config.database_url, future=True, pool_pre_ping=True)
    return _engine


def get_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(settings),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
