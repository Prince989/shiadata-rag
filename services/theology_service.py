from schemas.responses import ChatResponse, SourceNode
from pipelines.retrieval_pipeline import RetrievalPipeline


class TheologyService:
    def __init__(self):
        # راه‌اندازی موتور RAG (همون کدهای قبلی که به دیتابیس وصل می‌شد)
        # نکته: موتور رو فقط یک بار در حافظه لود می‌کنیم تا سرعت پاسخگویی بالا بره
        self.pipeline = RetrievalPipeline(db_directory="./data/chroma_db")

    def answer_question(self, question: str) -> ChatResponse:
        print(f"🧠 [TheologyService] Analyzing question: {question}")

        # فراخوانی تابع ask از پایپ‌لاین شما
        raw_result = self.pipeline.ask(question)

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