import logging

from schemas.responses import ChatResponse, SourceNode
from pipelines.retrieval_pipeline import RetrievalPipeline

logger = logging.getLogger(__name__)


class TheologyService:
    def __init__(self, container=None):
        # موتور RAG فقط یک بار در حافظه لود می‌شود (در lifespan)
        self.pipeline = RetrievalPipeline(container=container)

    def answer_question(
        self, question: str, collection: str | None = None, top_k: int | None = None
    ) -> ChatResponse:
        logger.info("analysing theology question (%d chars)", len(question))

        raw_result = self.pipeline.ask(question, collection=collection, top_k=top_k)

        # 🚑 [بخش ضدضربه]: اگر پایپ‌لاین شما فقط متنِ جواب رو برگردوند (نه دیکشنری)
        if isinstance(raw_result, str):
            raw_result = {
                "answer": raw_result,
                "sources": []  # فعلاً منابع رو خالی می‌ذاریم تا کرش نکنه
            }

        # ۲. تبدیل منابعِ خام به مدل استاندارد Pydantic (SourceNode)
        formatted_sources = []
        for src in raw_result.get("sources", []):
            formatted_sources.append(
                SourceNode(
                    book=src.get("book_title", "نامشخص"),
                    chapter=src.get("chapter", "نامشخص"),
                    footnotes=src.get("footnotes", None)
                )
            )

        # ۳. ساخت خروجی نهایی برای ارسال به دات‌نت
        return ChatResponse(
            answer=raw_result.get("answer", "پاسخی یافت نشد."),
            sources=formatted_sources,
            language_detected="fa"
        )