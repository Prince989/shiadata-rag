import json
import re
from services.hadith_service import HadithService
from services.rijal_service import RijalService
from services.quran_service import QuranService
from services.shawahid_service import ShawahidService
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List

print("⚙️ Initializing 2-Request Consolidated Ijtihad Engine...")
hadith_engine = HadithService()
rijal_engine = RijalService()
quran_engine = QuranService()
shawahid_engine = ShawahidService()
grand_mufti_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)

# ==========================================
# مدل خروجی مگا پرامپت (تجمیع شده)
# ==========================================
class NarratorAnalysis(BaseModel):
    name: str = Field(description="نام راوی")
    status: str = Field(description="وضعیت رجالی (مثلاً: صحیح، موثق، ضعیف، مجهول)")

class FinalIjtihadVerdict(BaseModel):
    narrators_status: List[NarratorAnalysis] = Field(description="تحلیل تک‌تک راویان بر اساس متون رجالی داده شده")
    sanad_status: str = Field(description="خلاصه وضعیت کل سند")
    quran_alignment: str = Field(description="وضعیت هم‌سویی با قرآن (با ذکر آیه)")
    shawahid_status: str = Field(description="وضعیت شواهد و متابعات")
    final_verdict: str = Field(description="حکم نهایی فقهی (صحیح، موثق، مقبول، ضعیف، احتیاط در انتساب، مردود)")
    detailed_reasoning: str = Field(description="استدلال جامع اصولی فقیهانه")

# ==========================================
# توابع استخراج خالص از دیتابیس (بدون مصرف LLM)
# ==========================================
def get_rijal_context_only(narrators: list[str]) -> str:
    print("   🔍 [DB] Hunting Rijal Context...")
    all_db_data = rijal_engine.vectorstore.get(include=["documents", "metadatas"])
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
            docs = rijal_engine.retriever.invoke(narrator_clean)
            for doc in docs[:2]:
                context_text += f"--- {doc.metadata.get('book_title')} ---\n{doc.page_content[:400]}\n"
    return context_text if context_text else "داده رجالی یافت نشد."

def get_quran_context_only(matn: str) -> str:
    print("   🕋 [DB] Hunting Quran Context...")
    docs = quran_engine.vectorstore.similarity_search(matn, k=4)
    return "\n".join([f"--- آیه ---\n{doc.page_content}" for doc in docs])

def get_shawahid_context_only(matn: str) -> str:
    print("   📚 [DB] Hunting Shawahid Context...")
    docs = shawahid_engine.vectorstore.similarity_search(matn, k=5)
    return "\n".join([f"--- حدیث یافت شده ---\n{doc.page_content[:300]}" for doc in docs])

# ==========================================
# پایپ‌لاین ادغام شده (فقط ۲ ریکوئست)
# ==========================================
def run_pipeline_consolidated(raw_hadith_text: str):
    print("\n" + "="*75)
    print("⚡ THE CONSOLIDATED IJTIHAD ENGINE (2 LLM Calls Only)")
    print("="*75)
    
    # --- ریکوئست اول ---
    print("\n1️⃣ [LLM CALL 1] Extracting Sanad & Matn...")
    extraction_result = hadith_engine.extract_sanad(raw_hadith_text)
    
    # --- عملیات دیتابیس (بدون ریکوئست به گوگل) ---
    print("\n2️⃣ [NO LLM] Gathering all Contexts from VectorDBs...")
    rijal_ctx = get_rijal_context_only(extraction_result.narrators)
    quran_ctx = get_quran_context_only(extraction_result.matn)
    shawahid_ctx = get_shawahid_context_only(raw_hadith_text)

    # --- ریکوئست دوم ---
    print("\n3️⃣ [LLM CALL 2] Sending Mega-Prompt to Grand Mufti...")
    
    prompt = f"""
    شما یک فقیه و مجتهد جامع‌الشرایط هستید. تمام داده‌های خام از دیتابیس‌ها برای شما جمع‌آوری شده است.
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
    ۱. ضعف طریق به کتاب راوی (مثل: ضعیف بابی المفضل) به معنای ضعف خود شخص نیست.
    ۲. اگر متن با قرآن در تعارض است، حدیث مردود است (حتی اگر سند صحیح باشد).
    ۳. اگر سند ضعیف است اما با قرآن همسو است و شواهد دارد، حدیث «معتبر/مقبول» است.
    ۴. اگر سند ضعیف است و شواهد هم ندارد، اما مفهومش با قرآن می‌خواند، حکم به «احتیاط در انتساب» بدهید.
    """
    
    structured_judge = grand_mufti_llm.with_structured_output(FinalIjtihadVerdict)
    final_verdict = structured_judge.invoke(prompt)

    # --- نمایش خروجی ---
    print("\n" + "🌟"*40)
    print("                 THE GRAND MUFTI VERDICT")
    print("🌟"*40)
    for narrator in final_verdict.narrators_status:
        print(f"👤 {narrator.name}: {narrator.status}")
    print("-"*40)
    print(f"⛓️ Sanad Status  : {final_verdict.sanad_status}")
    print(f"📖 Quran Status  : {final_verdict.quran_alignment}")
    print(f"📚 Shawahid      : {final_verdict.shawahid_status}")
    print(f"📌 Final Verdict : {final_verdict.final_verdict}")
    print(f"\n📝 Reasoning:\n{final_verdict.detailed_reasoning}")
    print("🌟"*40)


if __name__ == "__main__":
    prayer_hadith = "مُحَمَّدُ بْنُ يَحْيَى، عَنْ أَحْمَدَ بْنِ مُحَمَّدٍ، عَنِ ابْنِ مَحْبُوبٍ، عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ، عَنْ أَبِي عَبْدِ اللَّهِ (ع) قَالَ: لَيْسَ بَيْنَ الْمُسْلِمِ وَ بَيْنَ أَنْ يَكْفُرَ إِلَّا أَنْ يَتْرُكَ الصَّلَاةَ الْفَرِيضَةَ مُتَعَمِّداً."
    
    run_pipeline_consolidated(prayer_hadith)