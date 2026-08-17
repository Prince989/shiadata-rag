from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_theology_service
from schemas.requests import ChatRequest
from schemas.responses import ChatResponse

router = APIRouter(prefix="/api/v1/theology", tags=["Theology & Mahdawiyyat"])


@router.post("/ask", response_model=ChatResponse, summary="پاسخگویی به شبهات اعتقادی")
def ask_theology_question(
    request: ChatRequest,
    service=Depends(get_theology_service),
) -> ChatResponse:
    """
    Alias of POST /api/v1/chat, kept for existing callers.

    Both delegate to TheologyService.answer_question. /api/v1/chat is the
    canonical route; prefer it in new clients.
    """
    try:
        return service.answer_question(
            request.question, collection=request.collection, top_k=request.top_k
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
