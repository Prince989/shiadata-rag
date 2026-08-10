from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.hadith_service import HadithService
from schemas.responses import (
    SanadExtractionResponse,
    LifestyleBatchResponse,
    AutoTaggingResponse
)

# ---------------------------------------------------------
# مدل‌های ورودی (Requests) - معادل DTO در معماری تمیز
# ---------------------------------------------------------
class SingleTextRequest(BaseModel):
    text: str

class BatchHadithRequest(BaseModel):
    hadiths: List[str]

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
    domain_filter: Optional[str] = None

# ---------------------------------------------------------
# راه‌اندازی روتر و سرویس
# ---------------------------------------------------------
router = APIRouter(prefix="/api/v1/hadith", tags=["Hadith Engine"])

# در یک معماری پروداکشن، این سرویس معمولاً از طریق Dependency Injection (Depends) تزریق می‌شود
hadith_service = HadithService()

# ==========================================
# اندپوینت ۱: جراحی سند و متن
# ==========================================
@router.post("/extract-sanad", response_model=SanadExtractionResponse)
async def extract_sanad_endpoint(request: SingleTextRequest):
    """
    دریافت متن خام عربی و استخراج تفکیک‌شده‌ی سند، متن و حل ضمایر راویان.
    """
    try:
        result = hadith_service.extract_sanad(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

# ==========================================
# اندپوینت ۲: مشاور سبک زندگی
# ==========================================
@router.post("/lifestyle-advice", response_model=LifestyleBatchResponse)
async def lifestyle_advice_endpoint(request: BatchHadithRequest):
    """
    دریافت لیستی از احادیث و تولید توصیه‌های کاربردی و روان‌شناختی به صورت مجزا برای هر کدام.
    """
    try:
        result = hadith_service.generate_lifestyle_advice(request.hadiths)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

# ==========================================
# اندپوینت ۳: سیستم تگ‌زنی خودکار (CMS)
# ==========================================
@router.post("/auto-tag", response_model=AutoTaggingResponse)
async def auto_tag_endpoint(request: SingleTextRequest):
    """
    دریافت متن تاریخی/مذهبی و استخراج کلمات کلیدی، اشخاص و دامین برای گراف دانش.
    """
    try:
        result = hadith_service.auto_tag_document(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

# ==========================================
# اندپوینت ۴: موتور جستجوی معنایی
# ==========================================
@router.post("/search")
async def search_hadiths_endpoint(request: SearchRequest):
    """
    جستجوی هوشمند در دیتابیس برداری (ChromaDB) بر اساس مفهوم و دامین.
    """
    try:
        results = hadith_service.search_similar_hadiths(
            query=request.query,
            top_k=request.top_k,
            domain_filter=request.domain_filter
        )
        return {"total_found": len(results), "documents": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector DB Error: {str(e)}")