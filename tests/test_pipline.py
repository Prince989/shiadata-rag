import json
import time
from services.hadith_service import HadithService
from services.rijal_service import RijalService
from services.quran_service import QuranService
from services.shawahid_service import ShawahidService
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

print("⚙️ Initializing 4-Core Ijtihad Engine...")
hadith_engine = HadithService()
rijal_engine = RijalService()
quran_engine = QuranService()
shawahid_engine = ShawahidService()
grand_mufti_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)

class FinalIjtihadVerdict(BaseModel):
    sanad_status: str = Field(description="خلاصه وضعیت سند")
    quran_alignment: str = Field(description="خلاصه وضعیت هم‌سویی با قرآن")
    shawahid_status: str = Field(description="خلاصه وضعیت شواهد و تواتر روایی")
    final_verdict: str = Field(description="حکم نهایی فقهی (مثلاً: صحیح، موثق، مقبول، ضعیف، مردود)")
    detailed_reasoning: str = Field(description="استدلال جامع اصولی با ترکیب هر سه گزارش")

def run_pipeline_1_grand_ijtihad(raw_hadith_text: str):
    print("\n" + "="*75)
    print("⚖️ PIPELINE 1: THE ULTIMATE IJTIHAD ENGINE")
    print("="*75)
    
    # ---------------------------------------------------------
    print("\n1️⃣ [STEP 1] Extracting Sanad & Matn...")
    extraction_result = hadith_engine.extract_sanad(raw_hadith_text)
    print(f"   👤 Narrators: {extraction_result.narrators}")
    print(f"   📜 Matn: {extraction_result.matn}")

    print("\n⏳ (Micro-Delay: 15s to bypass API limits)...")
    time.sleep(15)

    # ---------------------------------------------------------
    print("\n2️⃣ [STEP 2] Rijal Validation (The 1st Filter)...")
    rijal_result = rijal_engine.validate_sanad(extraction_result.narrators)

    print("\n⏳ (Micro-Delay: 15s to bypass API limits)...")
    time.sleep(15)

    # ---------------------------------------------------------
    print("\n3️⃣ [STEP 3] Quranic Validation (The 2nd Filter)...")
    quran_result = quran_engine.validate_matn_with_quran(extraction_result.matn)

    print("\n⏳ (Micro-Delay: 15s to bypass API limits)...")
    time.sleep(15)

    # ---------------------------------------------------------
    print("\n4️⃣ [STEP 4] Shawahid & Mutaba'at (The 3rd Filter)...")
    shawahid_result = shawahid_engine.find_shawahid(raw_hadith_text)
    print(f"   📚 Corroboration Status: {shawahid_result['corroboration_status']}")

    print("\n⏳ (Micro-Delay: 15s to bypass API limits)...")
    time.sleep(15)

    # ---------------------------------------------------------
    print("\n5️⃣ [STEP 5] Synthesizing Final Ijtihad Verdict...")
    
    prompt = f"""
    شما یک فقیه، مجتهد اصولی و رجالیِ بسیار محتاط هستید.
    سه گزارش تخصصی درباره یک حدیث به شما ارجاع شده است. 
    وظیفه شما صدور حکم نهایی با در نظر گرفتن قواعد دقیق فقه الحدیث است.
    
    گزارش ۱: رجال (بررسی زنجیره سند):
    {json.dumps(rijal_result, ensure_ascii=False)}
    
    گزارش ۲: قرآن (عرضه بر کتاب الله):
    {json.dumps(quran_result, ensure_ascii=False)}
    
    گزارش ۳: شواهد و تواتر (بررسی احادیث مشابه):
    {json.dumps(shawahid_result, ensure_ascii=False)}
    
    ⚠️ قواعد استنباط (بسیار مهم):
    ۱. ضعف سندی به معنای جعلی بودن قطعی نیست.
    ۲. اگر سند ضعیف است، اما متن با قرآن «هم‌سو» است و در گزارش سوم «دارای شواهد» یا «مستفیض» تشخیص داده شده است، ضعف سند کاملاً جبران می‌شود و حدیث "صحیح و معتبر" (محفوف به قرائن) است.
    ۳. اگر سند ضعیف است، با قرآن هم‌سو است، اما در گزارش سوم "غریب/منفرد" است، حکم به "احتیاط در انتساب" بدهید.
    ۴. اگر با قرآن در تعارض است، مطلقاً مردود است.
    ۵. اگر سند "صحیح" است و با قرآن هم‌سو است، حدیث کاملاً قطعی و صحیح است.
    """
    
    structured_judge = grand_mufti_llm.with_structured_output(FinalIjtihadVerdict)
    final_verdict = structured_judge.invoke(prompt)

    # ---------------------------------------------------------
    print("\n" + "🌟"*40)
    print("                 THE GRAND MUFTI VERDICT")
    print("🌟"*40)
    print(f"⛓️ Sanad Status  : {final_verdict.sanad_status}")
    print(f"📖 Quran Status  : {final_verdict.quran_alignment}")
    print(f"📚 Shawahid      : {final_verdict.shawahid_status}")
    print(f"📌 Final Verdict : {final_verdict.final_verdict}")
    print(f"\n📝 Reasoning:\n{final_verdict.detailed_reasoning}")
    print("🌟"*40)


if __name__ == "__main__":
    # تست سوم (سند فولادین، متن قطعی درباره ترک نماز)
    prayer_hadith = "مُحَمَّدُ بْنُ يَحْيَى، عَنْ أَحْمَدَ بْنِ مُحَمَّدٍ، عَنِ ابْنِ مَحْبُوبٍ، عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ، عَنْ أَبِي عَبْدِ اللَّهِ (ع) قَالَ: لَيْسَ بَيْنَ الْمُسْلِمِ وَ بَيْنَ أَنْ يَكْفُرَ إِلَّا أَنْ يَتْرُكَ الصَّلَاةَ الْفَرِيضَةَ مُتَعَمِّداً."
    
    print("\n▶️ اجرای تست حدیث السلسلة الذهبية (ترک نماز)...")
    run_pipeline_1_grand_ijtihad(prayer_hadith)