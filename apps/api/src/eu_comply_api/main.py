from contextlib import asynccontextmanager

from fastapi import FastAPI

from eu_comply_api.api.router import api_router
from eu_comply_api.config import get_settings
from eu_comply_api.core.logging import configure_logging
from eu_comply_api.db.bootstrap import bootstrap_defaults
from eu_comply_api.db.models import Base
from eu_comply_api.db.session import get_engine, get_session_factory


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    settings = get_settings()
    if settings.auto_create_schema:
        engine = get_engine(settings)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        await bootstrap_defaults(session, settings)
        await session.commit()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        }

    return app


app = create_app()
