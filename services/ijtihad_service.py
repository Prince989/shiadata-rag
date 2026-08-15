import json
import re
from pydantic import BaseModel, Field
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI

# ایمپورت سرویس‌های پایه
from services.hadith_service import HadithService
from services.rijal_service import RijalService
from services.quran_service import QuranService
from services.shawahid_service import ShawahidService

# --- Pydantic Schemas برای خروجی API ---
class NarratorAnalysis(BaseModel):
    name: str = Field(description="نام راوی")
    status: str = Field(description="وضعیت رجالی (مثلاً: صحیح، موثق، ضعیف، مجهول)")

class FinalIjtihadVerdict(BaseModel):
    narrators_status: List[NarratorAnalysis] = Field(description="تحلیل تک‌تک راویان")
    sanad_status: str = Field(description="خلاصه وضعیت کل سند")
    quran_alignment: str = Field(description="وضعیت هم‌سویی با قرآن (با ذکر آیه)")
    shawahid_status: str = Field(description="وضعیت شواهد و متابعات")
    final_verdict: str = Field(description="حکم نهایی فقهی")
    detailed_reasoning: str = Field(description="استدلال جامع اصولی فقیهانه")

class IjtihadService:
    def __init__(self):
        self.hadith_engine = HadithService()
        self.rijal_engine = RijalService()
        self.quran_engine = QuranService()
        self.shawahid_engine = ShawahidService()
        self.llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)

    def _get_rijal_context(self, narrators: list[str]) -> str:
        all_db_data = self.rijal_engine.vectorstore.get(include=["documents", "metadatas"])
        context_text = ""
        for narrator in narrators:
            narrator_clean = narrator.strip()
            n_fa = narrator_clean.replace("ي", "ی").replace("ك", "ک").replace("أ", "ا")
            n_ar = narrator_clean.replace("ی", "ي").replace("ک", "ك").replace("ا", "أ")
            
            exact_matches = []
            from langchain_core.documents import Document
            for text, meta in zip(all_db_data["documents"], all_db_data["metadatas"]):
                if narrator_clean in text or n_fa in text or n_ar in text:
                    exact_matches.append(Document(page_content=text, metadata=meta))
            
            if exact_matches:
                def score_doc(doc):
                    text = doc.page_content
                    score = 100 if re.search(r'(^|\n|\-)\s*' + re.escape(narrator_clean), text) else 0
                    if any(word in text for word in ["=", "ضعيف", "ثقة", "صحيح", "مجهول"]): score += 50
                    return score - (len(text) / 1000)
                
                exact_matches.sort(key=score_doc, reverse=True)
                for doc in exact_matches[:3]:
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
        
        structured_judge = self.llm.with_structured_output(FinalIjtihadVerdict)
        final_verdict = structured_judge.invoke(prompt)
        
        return final_verdict.model_dump()