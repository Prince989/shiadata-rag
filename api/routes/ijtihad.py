from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.ijtihad_service import IjtihadService

router = APIRouter()

# نمونه‌سازی از ارکستراتور (هنگام بالا آمدن سرور اینیشیالایز می‌شود)
ijtihad_service = IjtihadService()

# --- Schemas ---
class IjtihadRequest(BaseModel):
    text: str = Field(..., description="متن کامل عربی حدیث به همراه سند")

@router.post("/grand-ijtihad", summary="اعتبارسنجی جامع فقهی و رجالی (Ijtihad Engine)")
async def grand_ijtihad_endpoint(request: IjtihadRequest):
    """
    این اندپوینت یک حدیث خام را دریافت کرده و با استفاده از ۴ موتور (جراحی، رجال، قرآن و شواهد) 
    حکم نهایی فقهی را به صورت ساختاریافته برمی‌گرداند.
    """
    try:
        result = ijtihad_service.process_ijtihad(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))