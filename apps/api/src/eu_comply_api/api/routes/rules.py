from fastapi import APIRouter, Depends, HTTPException, status

from eu_comply_api.api.deps import AuthContext, require_auth_context
from eu_comply_api.domain.models import RulePackDetail, RulePackSummary
from eu_comply_api.services.rule_pack_service import RulePackService

router = APIRouter()


@router.get("/rule-packs", response_model=list[RulePackSummary])
async def list_rule_packs(
    _: AuthContext = Depends(require_auth_context),
) -> list[RulePackSummary]:
    service = RulePackService()
    return await service.list_rule_packs()


@router.get("/rule-packs/{pack_id}", response_model=RulePackDetail)
async def get_rule_pack(
    pack_id: str,
    _: AuthContext = Depends(require_auth_context),
) -> RulePackDetail:
    service = RulePackService()
    pack = await service.get_rule_pack(pack_id)
    if pack is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule pack '{pack_id}' was not found.",
        )
    return pack
