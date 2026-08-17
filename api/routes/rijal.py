from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_rijal_service
from schemas.requests import SanadValidationRequest
from schemas.responses import SanadValidationResponse

router = APIRouter(prefix="/api/v1/rijal", tags=["Ilm al-Rijal (Hadith Validation)"])


@router.post(
    "/validate",
    response_model=SanadValidationResponse,
    summary="اعتبارسنجی سند احادیث",
)
def validate_hadith_sanad(
    request: SanadValidationRequest,
    service=Depends(get_rijal_service),
):
    """
    Takes a list of narrator names, looks each one up in the rijal corpus and
    returns a per-narrator verdict plus an overall judgement.

    HEAVY: this route scans the whole rijal index and then makes an LLM call.
    Callers should treat it like the ijtihad routes, not like a search.
    """
    try:
        return service.validate_sanad(request.sanad_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
