import logging
import re
from typing import List

from pydantic import BaseModel, Field

# ایمپورت سرویس‌های پایه
from services.hadith_service import HadithService
from services.rijal_service import RijalService
from services.quran_service import QuranService
from services.shawahid_service import ShawahidService
from services.llm_gateway import LLMGateway

# Schemas live in schemas/responses.py so a single class serves as both the
# LLM structured-output schema and the FastAPI response_model.
from schemas.responses import NarratorAnalysis, IjtihadVerdictResponse

logger = logging.getLogger(__name__)

# Backwards-compatible alias for the manual scripts under scripts/manual/.
FinalIjtihadVerdict = IjtihadVerdictResponse


class IjtihadService:
    def __init__(self, container=None):
        # Reuse the container's already-built engines rather than constructing
        # a second HadithService and a third RijalService, each with their own
        # Chroma handle and embeddings client.
        if container is not None:
            self.hadith_engine = container.hadith or HadithService(container=container)
            self.rijal_engine = container.rijal or RijalService(container=container)
        else:
            self.hadith_engine = HadithService()
            self.rijal_engine = RijalService()

        self.quran_engine = QuranService(container=container)
        self.shawahid_engine = ShawahidService(container=container)

        # Routed through the gateway so these calls participate in key rotation
        # and retries. This used to instantiate ChatGoogleGenerativeAI directly,
        # bypassing the pool on the single most expensive call in the service.
        self.gateway = LLMGateway()

    def _get_rijal_context(self, narrators: list[str]) -> str:
        index = getattr(self.rijal_engine.container, "rijal_index", None) if getattr(
            self.rijal_engine, "container", None
        ) else None

        context_text = ""
        for narrator in narrators:
            narrator_clean = narrator.strip()

            exact_matches = index.lookup(narrator_clean, limit=3) if index else []

            if exact_matches:
                for doc in exact_matches:
                    context_text += f"--- {doc.metadata.get('book_title')} ---\n{doc.page_content[:400]}\n"
            else:
                docs = self.rijal_engine.retriever.invoke(narrator_clean)
                for doc in docs[:2]:
                    context_text += f"--- {doc.metadata.get('book_title')} ---\n{doc.page_content[:400]}\n"
        return context_text if context_text else "داده رجالی یافت نشد."

    def _get_quran_context(self, matn: str) -> str:
        docs = self.quran_engine.vectorstore.similarity_search(matn, k=4)
        return "\n".join([f"--- آیه ---\n{doc.page_content}" for doc in docs])

    def _get_shawahid_context(self, matn: str) -> str:
        docs = self.shawahid_engine.vectorstore.similarity_search(matn, k=5)
        return "\n".join([f"--- حدیث یافت شده ---\n{doc.page_content[:300]}" for doc in docs])

    def process_ijtihad(self, raw_hadith_text: str) -> dict:
        # ۱. استخراج سند و متن (درخواست اول به LLM)
        extraction_result = self.hadith_engine.extract_sanad(raw_hadith_text)
        
        # ۲. جمع‌آوری داده‌های خام از دیتابیس‌ها (بدون LLM)
        rijal_ctx = self._get_rijal_context(extraction_result.narrators)
        quran_ctx = self._get_quran_context(extraction_result.matn)
        shawahid_ctx = self._get_shawahid_context(raw_hadith_text)

        # ۳. صدور حکم نهایی (درخواست دوم به LLM)
        prompt = f"""
        شما یک فقیه و مجتهد جامع‌الشرایط هستید. تمام داده‌های خام از دیتابیس‌ها جمع‌آوری شده است.
        متن اصلی حدیث: {extraction_result.matn}
        راویان استخراج شده: {extraction_result.narrators}
        
        داده‌های رجالی یافت شده:
        {rijal_ctx}
        
        آیات مرتبط یافت شده در قرآن:
        {quran_ctx}
        
        احادیث مشابه یافت شده (شواهد):
        {shawahid_ctx}
        
        وظیفه شما پردازش همزمان این داده‌ها و صدور حکم نهایی است.
        قوانین:
        ۱. ضعف طریق به کتاب راوی به معنای ضعف خود شخص نیست.
        ۲. اگر متن با قرآن در تعارض صریح است، حدیث مردود است.
        ۳. اگر سند ضعیف است اما با قرآن همسو است و شواهد دارد، حدیث «معتبر/مقبول» است.
        ۴. اگر سند ضعیف است و شواهد هم ندارد، اما مفهومش با قرآن می‌خواند، حکم به «احتیاط در انتساب» بدهید.
        ۵. اگر سند صحیح است، فارغ از منفرد بودن، در صورت عدم تعارض با قرآن، حدیث «صحیح» است.
        """
        
        final_verdict = self.gateway.invoke_structured(
            prompt=prompt, schema_class=IjtihadVerdictResponse
        )
        return final_verdict.model_dump()