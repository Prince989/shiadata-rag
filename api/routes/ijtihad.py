from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import get_conflict_service, get_ijtihad_service
from schemas.responses import ConflictResolutionResponse, IjtihadVerdictResponse

# Previously this router had no prefix AND was included with no prefix, so both
# endpoints were mounted at the bare root rather than under /api/v1.
router = APIRouter(prefix="/api/v1/ijtihad", tags=["Ijtihad Engine"])


class IjtihadRequest(BaseModel):
    text: str = Field(..., min_length=10, description="متن کامل عربی حدیث به همراه سند")


class ConflictRequest(BaseModel):
    hadith1: str = Field(..., min_length=10, description="متن کامل عربی حدیث اول")
    hadith2: str = Field(..., min_length=10, description="متن کامل عربی حدیث دوم")


@router.post(
    "/grand-ijtihad",
    response_model=IjtihadVerdictResponse,
    summary="اعتبارسنجی جامع فقهی و رجالی (Ijtihad Engine)",
)
def grand_ijtihad_endpoint(
    request: IjtihadRequest,
    service=Depends(get_ijtihad_service),
):
    """
    Runs a hadith through four engines (sanad extraction, rijal, quran,
    shawahid) and returns a structured verdict.

    HEAVY: two LLM calls plus a full rijal scan. Expect tens of seconds.
    """
    try:
        return service.process_ijtihad(request.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/conflict-resolution",
    response_model=ConflictResolutionResponse,
    summary="حل تعارض بین دو حدیث (Conflict Resolver Engine)",
)
def conflict_endpoint(
    request: ConflictRequest,
    service=Depends(get_conflict_service),
):
    """
    Applies the usuli rules of ta'adul wa tarajih to two conflicting hadiths.

    HEAVY: one LLM call plus two full rijal scans.
    """
    try:
        return service.resolve_conflict(request.hadith1, request.hadith2)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
