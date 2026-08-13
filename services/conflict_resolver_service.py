import os
import re
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

# ایمپورت‌های اضافی لانگ‌چین رو حذف کردیم
from services.llm_gateway import LLMGateway
from services.rijal_service import RijalService
from services.quran_service import QuranService

load_dotenv()

# --- Schemas ---
class HadithSingleAnalysis(BaseModel):
    narrators: List[str] = Field(description="لیست راویان استخراج شده")
    matn: str = Field(description="متن خالص حدیث")
    sanad_status: str = Field(description="وضعیت سندی (صحیح، موثق، ضعیف، مجهول)")

class ConflictResolutionVerdict(BaseModel):
    hadith_1_analysis: HadithSingleAnalysis = Field(description="تحلیل سند و متن حدیث اول")
    hadith_2_analysis: HadithSingleAnalysis = Field(description="تحلیل سند و متن حدیث دوم")
    is_conflict_detected: bool = Field(description="آیا تعارض غیرقابل جمع وجود دارد؟")
    sanad_comparison: str = Field(description="مقایسه سندی دو حدیث")
    quran_tarjih: str = Field(description="سنجش و هم‌سویی با ظاهر آیات قرآن")
    taqiyyah_analysis: str = Field(description="تحلیل احتمال تقیه (موافق یا مخالف عامه/حاکمیت وقت)")
    tarjih_rule_applied: str = Field(description="قاعده اصولی بکار رفته (مرجح سندی، مرجح قرآنی، حمل بر تقیه، جمع دلالی)")
    final_verdict: str = Field(description="حکم نهایی فقهی")
    detailed_reasoning: str = Field(description="استدلال جامع اصولی و فقهی")

class ConflictResolverService:
    def __init__(self):
        self.rijal_engine = RijalService()
        self.quran_engine = QuranService()
        
        # 👈 ۱. فقط Gateway را نمونه‌سازی می‌کنیم
        self.gateway = LLMGateway()

        # 👈 ۲. پرامپت‌ها را به جای شیء لانگ‌چین، به استرینگ‌های پایتونی تبدیل می‌کنیم
        self.system_prompt = """شما یک اصولی و مجتهد تراز اول شیعه متخصص در «باب تعادل و تراجیح» هستید.
تمام داده‌های خام متنی، رجالی و قرآنی از دیتابیس استخراج شده و در اختیار شماست.
وظیفه شما کالبدشکافی دو حدیث، تحلیل سند و متن هرکدام و تعیین تکلیف تعارض طبق مرجّحات اصولی است.

⚠️ مرجّحات اصولی به ترتیب اولویت:
۱. **مرجّح سندی:** اگر سند یکی صحیح و دیگری ضعیف باشد، حدیث صحیح اخذ و ضعیف طرح می‌گردد.
۲. **جمع دلالی (اولویّت بر طرح):** «الجمع مهما امکن اولی من الطرح». اگر امکان جمع عرفی وجود دارد (مثل عام و خاص، یا حمل وجوب بر استحباب)، جمع دلالی کنید.
۳. **مرجّح قرآنی (موافقت کتاب):** اگر تعارض مستقر بود، روایتی که موافق ظاهر قرآن است ترجیح داده می‌شود.
۴. **مرجّح جهتی (مخالفت عامه/تقیه):** روایتی که مخالف فتوای اهل سنت و حکومت وقت باشد ترجیح داده می‌شود (روایت موافق عامه احتمالاً از روی تقیه است).

پاسخ باید کاملاً اصولی، علمی، دقیق و به زبان فارسی باشد.
"""

        self.user_prompt_template = """دو حدیث زیر را بررسی کن:

📜 **حدیث اول:**
{hadith_1_raw}

داده‌های رجالی حدیث اول از دیتابیس:
{rijal_1_ctx}

آیات مرتبط با حدیث اول از دیتابیس:
{quran_1_ctx}

---

📜 **حدیث دوم:**
{hadith_2_raw}

داده‌های رجالی حدیث دوم از دیتابیس:
{rijal_2_ctx}

آیات مرتبط با حدیث دوم از دیتابیس:
{quran_2_ctx}
"""

    def _extract_narrators_python(self, text: str) -> List[str]:
        if "عن" in text:
            parts = text.split("قال")[0].split("عن")
            return [p.strip() for p in parts if len(p.strip()) > 3]
        return [text[:50]]

    def _get_rijal_context_python(self, narrators: List[str]) -> str:
        all_db_data = self.rijal_engine.vectorstore.get(include=["documents", "metadatas"])
        context_text = ""
        for narrator in narrators:
            narrator_clean = narrator.strip()
            n_fa = narrator_clean.replace("ي", "ی").replace("ك", "ک").replace("أ", "ا")
            n_ar = narrator_clean.replace("ی", "ي").replace("ک", "ك").replace("ا", "أ")
            
            from langchain_core.documents import Document
            exact_matches = []
            for doc_text, meta in zip(all_db_data["documents"], all_db_data["metadatas"]):
                if narrator_clean in doc_text or n_fa in doc_text or n_ar in doc_text:
                    exact_matches.append(Document(page_content=doc_text, metadata=meta))
            
            if exact_matches:
                for doc in exact_matches[:2]:
                    context_text += f"--- {doc.metadata.get('book_title', 'رجال')} ---\n{doc.page_content[:300]}\n"
            else:
                docs = self.rijal_engine.retriever.invoke(narrator_clean)
                for doc in docs[:1]:
                    context_text += f"--- {doc.metadata.get('book_title', 'رجال')} ---\n{doc.page_content[:300]}\n"
        return context_text if context_text else "داده رجالی یافت نشد."

    def _get_quran_context_python(self, text: str) -> str:
        docs = self.quran_engine.vectorstore.similarity_search(text, k=3)
        return "\n".join([f"--- آیه ---\n{doc.page_content}" for doc in docs])

    def resolve_conflict(self, hadith_text_1: str, hadith_text_2: str) -> dict:
        print("\n🔍 [Python DB Search] Fetching contexts for Hadith 1...")
        narrators_1 = self._extract_narrators_python(hadith_text_1)
        rijal_1_ctx = self._get_rijal_context_python(narrators_1)
        quran_1_ctx = self._get_quran_context_python(hadith_text_1)

        print("🔍 [Python DB Search] Fetching contexts for Hadith 2...")
        narrators_2 = self._extract_narrators_python(hadith_text_2)
        rijal_2_ctx = self._get_rijal_context_python(narrators_2)
        quran_2_ctx = self._get_quran_context_python(hadith_text_2)

        print("\n🚀 [SINGLE LLM CALL] Executing Consolidated Conflict Resolution via LLMGateway...")
        
        # 👈 ۳. مقادیر را در قالب متنی جاگذاری می‌کنیم
        final_user_prompt = self.user_prompt_template.format(
            hadith_1_raw=hadith_text_1,
            rijal_1_ctx=rijal_1_ctx,
            quran_1_ctx=quran_1_ctx,
            hadith_2_raw=hadith_text_2,
            rijal_2_ctx=rijal_2_ctx,
            quran_2_ctx=quran_2_ctx,
        )
        
        # ترکیب پرامپت سیستم و پرامپت کاربر
        full_prompt = f"{self.system_prompt}\n\n{final_user_prompt}"

        try:
            # 👈 ۴. صدا زدن Gateway با متدی که در `llm_gateway.py` ساختیم!
            response_obj = self.gateway.invoke_structured(
                prompt=full_prompt, 
                schema_class=ConflictResolutionVerdict
            )
            return response_obj.model_dump()
            
        except Exception as e:
            print(f"❌ Conflict Resolver Gateway Error: {e}")
            raise e