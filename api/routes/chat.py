"""
Canonical RAG chat endpoint.

This replaces the previous handler in main.py, which was a terminal REPL
(`while True: input(...)`) wired to an HTTP verb. Under uvicorn that raised
EOFError or blocked a threadpool worker forever, and since it declared a
response_model it also appeared in the OpenAPI document and would have been
code-generated into any client.
"""

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_theology_service
from schemas.requests import ChatRequest
from schemas.responses import ChatResponse

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, summary="پرسش و پاسخ مبتنی بر منابع")
def chat(
    request: ChatRequest,
    service=Depends(get_theology_service),
) -> ChatResponse:
    try:
        return service.answer_question(
            request.question, collection=request.collection, top_k=request.top_k
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
