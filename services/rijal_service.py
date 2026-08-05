from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from schemas.responses import SanadValidationResponse
from dotenv import load_dotenv
import os

load_dotenv()
print(f"🔑 Loaded Key: {os.getenv('GOOGLE_API_KEY')[:10]}... (truncated)")

class RijalService:
    def __init__(self):
        # اتصال به سطل مخصوص رجال
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = Chroma(
            persist_directory="./data/chroma_db",
            embedding_function=self.embeddings,
            collection_name="rijal"
        )
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 20,           # تعداد نتایج نهایی که به هوش مصنوعی داده میشه
                "fetch_k": 50,     # اول ۵۰ تا نتیجه مرتبط پیدا میکنه، بعد متنوع‌ترین ۲۰ تا رو گلچین میکنه
                "lambda_mult": 0.5 # ضریب تنوع (نیم یعنی بالانس کامل بین ربط داشتن و متنوع بودن)
            }
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            temperature=0,
            max_retries=2
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """شما یک رباتِ استخراج‌گرِ داده هستید و مطلقاً حق استفاده از دانش قبلی خود را ندارید.
        شما باید فقط و فقط بر اساس متون یافت شده زیر پاسخ دهید:
        {context}

        ⚠️ قوانین حیاتی (Strict Instructions):
        ۱. زبان خروجی: تمام تحلیل‌ها و خروجی‌ها باید به زبان فارسی باشد.
        ۲. ممنوعیت توهم: اگر در متون صراحتاً وضعیتی برای راوی ذکر نشده باشد، او را "مجهول" اعلام کنید.
        ۳. جعل منبع: ذکر هر منبعی خارج از تگ‌های (--- منبع ---) خطای مرگبار است.
        ۴. مرزبندی راویان: اطلاعاتِ هر راوی دقیقاً قبل از شروعِ شماره‌ی بعدی به پایان می‌رسد.
        ۵. 💡 درک فرمت‌های اختصاصی (بسیار مهم): در برخی متون، وضعیت راوی مستقیماً بعد از علامت مساوی (=) نوشته شده است (مثلاً "نام راوی. = ضعيف" یا "نام راوی. = صحيح"). در این حالت، شما موظف هستید دقیقاً همان کلمه بعد از مساوی را به عنوان «وضعیت راوی» در نظر بگیرید و از تفسیرهای اضافی (مثلاً اینکه این کلمه مربوط به طریق است نه شخص) خودداری کنید.
        ۶. 📚 تجمیع منابع (بسیار مهم): اگر اطلاعات یک راوی در چندین منبعِ مختلف از متون بالا تکرار شده است، شما موظف هستید نام و آدرس دقیقِ **تمام آن منابع** را در بخش source درج کنید (مثلاً: معجم رجال الحدیث ج ۵ ص ۱۰ و الفهرست ص ۳۰۰). به هیچ وجه به یک منبع اکتفا نکنید.
             
        وظیفه شما:
        ۱. نام راوی.
        ۲. وضعیت راوی (ثقه، ضعیف، مجهول، ممدوح، صحیح) دقیقاً بر اساس کانتکست.
        ۳. نظر علما (کپی دقیق از کانتکست).
        ۴. حکم کلی سند.
        """),
            ("human", "سند برای بررسی: {sanad}")
        ])

    def validate_sanad(self, sanad_text: str) -> dict:
        print(f"\n🔍 [RijalService] Analyzing Sanad: {sanad_text}")

        # ==========================================
        # 🚀 اصلاح بنیادین گام اول و دوم: حفظ نام‌های مرکب
        # ==========================================
        print("📚 Step 2: Smart Searching without breaking compound names...")
        all_docs = []

        # ۱. جستجوی خودِ عبارت کاملِ ورودی کاربر (به عنوان اولین و قوی‌ترین کوئری)
        all_docs.extend(self.retriever.invoke(sanad_text))

        # ۲. اگر کلمه «عن» در سند وجود دارد، راویان را از روی «عن» جدا می‌کنیم
        # (دیگر کلمات داخل نام مثل عبدالله یا سعد از هم خرد نمی‌شوند!)
        if "عن" in sanad_text:
            narrators = [n.strip() for n in sanad_text.split("عن") if n.strip()]
        else:
            narrators = [sanad_text]

        print(f"   ✔️ Target Search Entities: {narrators}")
# استخراج کل دیتابیس در حافظه (Brute-force Search)
        print("   📥 Fetching entire Vector DB for exact memory match...")
        all_db_data = self.vectorstore.get(include=["documents", "metadatas"])
        
        for narrator in narrators:
            # حذف فاصله‌های اضافی
            narrator_clean = narrator.strip()
            
            # ساخت نسخه‌های مختلف اسم برای خنثی کردن باگِ ی/ي و أ/ا
            n_fa = narrator_clean.replace("ي", "ی").replace("ك", "ک").replace("أ", "ا")
            n_ar = narrator_clean.replace("ی", "ي").replace("ک", "ك").replace("ا", "أ")
            
            print(f"   🔍 Memory Hunting for: '{narrator_clean}'")
            
            exact_matches = []
            from langchain_core.documents import Document
            
            # جستجوی خط به خط در کل دیتابیس (Ctrl+F واقعی)
            for text, meta in zip(all_db_data["documents"], all_db_data["metadatas"]):
                if narrator_clean in text or n_fa in text or n_ar in text:
                    exact_matches.append(Document(page_content=text, metadata=meta))
            
            if exact_matches:
                print(f"      ✅ BINGO! Found {len(exact_matches)} absolute exact matches in memory!")
                
                # 🚀 الگوریتم امتیازدهی برای پیدا کردن متن‌های اصلی رجالی
                import re
                def score_doc(doc):
                    text = doc.page_content
                    score = 0
                    
                    # ۱. امتیاز طلایی (+100): اگر اسم راوی اول خط باشه، یا بعد از خط تیره و عدد باشه (یعنی تیتر اصلیه)
                    if re.search(r'(^|\n|\-)\s*' + re.escape(narrator_clean), text):
                        score += 100
                    if re.search(r'(^|\n|\-)\s*' + re.escape(n_ar), text):
                        score += 100
                        
                    # ۲. امتیاز نقره‌ای (+50): اگر تو همون چانک، کلمات کلیدیِ ارزیابی باشه
                    if any(word in text for word in ["=", "ضعيف", "ثقة", "ثقه", "صحيح", "مجهول"]):
                        score += 50
                        
                    # ۳. جریمه (-): متن‌های خیلی طولانی معمولاً پاراگراف‌های بی‌ربط هستن، پس امتیازشون کم میشه
                    score -= len(text) / 1000 
                    
                    return score
                
                # 🛠 مرتب‌سازی ۱۰۴ نتیجه بر اساس بالاترین امتیاز رجالی
                exact_matches.sort(key=score_doc, reverse=True)
                
                # حالا ۵ تای اول، قطعاً همون لیست‌های اسکرپ‌شده و تیترهای اصلیِ معجم هستن
                all_docs.extend(exact_matches[:5])
                
                # چاپ لاگ برای اطمینان از اینکه متنِ درست انتخاب شده
                print(f"      🏆 Top Match Preview: {exact_matches[0].page_content[:60].strip()}...")

            else:
                print(f"      ⚠️ No exact match anywhere. Falling back to Vector Search...")
                all_docs.extend(self.retriever.invoke(narrator_clean))

        # حذف صفحات تکراری و ساخت کانتکست تمیز
        unique_pages = set()
        context_text = ""

        for doc in all_docs:
            page_ref = doc.metadata.get('chapter', 'Unknown Page')
            if page_ref not in unique_pages:
                unique_pages.add(page_ref)
                chunk_text = doc.page_content.strip()
                if chunk_text and len(chunk_text) > 20:  # حذف نویزهای خیلی کوتاه
                    context_text += f"--- منبع ({doc.metadata.get('book_title')} - {page_ref}) ---\n{chunk_text}\n\n"

        if not context_text:
            context_text = "هیچ متنی در دیتابیس یافت نشد."

        # چاپ کانتکست برای اطمینان خاطر
        print("\n" + "=" * 50)
        print("📥 CONTEXT SENT TO LLM:")
        print("=" * 50)
        print(context_text)
        print("=" * 50 + "\n")

        # ==========================================
        # 🤖 گام سوم: ارسال به قاضی نهایی
        # ==========================================
        print("🤖 Step 3: Synthesizing AI Verdict...")
        chain = self.prompt | self.llm.with_structured_output(SanadValidationResponse)

        try:
            response_obj = chain.invoke({"context": context_text, "sanad": sanad_text})
            return response_obj.model_dump()
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            raise e

        #AQ.Ab8RN6LM2Qn4VEysXvlrOEQq9iPtetGVigHzdZ34mQvLnCq7RA