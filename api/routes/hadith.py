"""
Hadith engine routes.

Every handler here is a plain `def`, not `async def`. They call fully
synchronous LLM and ChromaDB code with no await, so declaring them async put
that blocking work directly on the event loop -- one request froze the whole
process, /health included. FastAPI runs plain `def` handlers in a threadpool,
which is the correct home for blocking I/O.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import get_hadith_service
from schemas.responses import (
    AutoTaggingResponse,
    LifestyleBatchResponse,
    SanadExtractionResponse,
    SearchResponse,
)
from services.search_utils import to_retrieved_document

router = APIRouter(prefix="/api/v1/hadith", tags=["Hadith Engine"])


class SingleTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000)


class BatchHadithRequest(BaseModel):
    hadiths: List[str] = Field(..., min_length=1, max_length=50)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=8_000)
    top_k: int = Field(default=3, ge=1, le=50)
    domain_filter: Optional[str] = None


@router.post("/extract-sanad", response_model=SanadExtractionResponse)
def extract_sanad_endpoint(
    request: SingleTextRequest,
    service=Depends(get_hadith_service),
):
    """دریافت متن خام عربی و استخراج تفکیک‌شده‌ی سند، متن و حل ضمایر راویان."""
    try:
        return service.extract_sanad(request.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {exc}")


@router.post("/lifestyle-advice", response_model=LifestyleBatchResponse)
def lifestyle_advice_endpoint(
    request: BatchHadithRequest,
    service=Depends(get_hadith_service),
):
    """
    دریافت لیستی از احادیث و تولید توصیه‌های کاربردی و روان‌شناختی.

    Note: this is a batch call -- all hadiths go into a single LLM request, so
    a long list means one long generation and a real truncation risk.
    """
    try:
        return service.generate_lifestyle_advice(request.hadiths)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {exc}")


@router.post("/auto-tag", response_model=AutoTaggingResponse)
def auto_tag_endpoint(
    request: SingleTextRequest,
    service=Depends(get_hadith_service),
):
    """استخراج کلمات کلیدی، اشخاص و دامین برای گراف دانش."""
    try:
        return service.auto_tag_document(request.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {exc}")


@router.post(
    "/search",
    response_model=SearchResponse,
    deprecated=True,
    summary="[Deprecated] از POST /api/v1/search استفاده کنید",
)
def search_hadiths_endpoint(
    request: SearchRequest,
    service=Depends(get_hadith_service),
):
    """
    Deprecated in favour of the generic POST /api/v1/search, which supports
    every collection and richer filters. Kept so existing callers keep working.
    """
    try:
        docs = service.search_similar_hadiths(
            query=request.query,
            top_k=request.top_k,
            domain_filter=request.domain_filter,
        )
        return SearchResponse(
            collection="hadith",
            query=request.query,
            total_found=len(docs),
            documents=[to_retrieved_document(doc) for doc in docs],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vector DB Error: {exc}")
