from fastapi import APIRouter, HTTPException
from schemas.requests import SanadValidationRequest
from schemas.responses import SanadValidationResponse
from services.rijal_service import RijalService

router = APIRouter()
rijal_service = RijalService()

@router.post("/validate", response_model=SanadValidationResponse, summary="اعتبارسنجی سند احادیث")
def validate_hadith_sanad(request: SanadValidationRequest):
    """
    این API نام راویان یا یک سند عربی را دریافت کرده، در دیتابیس رجال شیعه
    (مانند معجم رجال الحدیث) جستجو می‌کند و وضعیت اعتبار آن‌ها را برمی‌گرداند.
    """
    try:
        response_dict = rijal_service.validate_sanad(request.sanad_text)
        return response_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))