from fastapi import APIRouter

from eu_comply_api.api.routes import (
    artifacts,
    assessments,
    auth,
    cases,
    health,
    policy,
    rules,
    runtime,
    workflows,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(cases.router, tags=["cases"])
api_router.include_router(artifacts.router, tags=["artifacts"])
api_router.include_router(assessments.router, tags=["assessments"])
api_router.include_router(workflows.router, tags=["workflows"])
api_router.include_router(runtime.router, prefix="/runtime", tags=["runtime"])
api_router.include_router(policy.router, tags=["policy"])
api_router.include_router(rules.router, tags=["rules"])
