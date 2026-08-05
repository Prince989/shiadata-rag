from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from schemas.responses import SanadValidationResponse
from dotenv import load_dotenv

load_dotenv()

class RijalService:
    def __init__(self):
        # اتصال به سطل مخصوص رجال
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = Chroma(
            persist_directory="./data/chroma_db",
            embedding_function=self.embeddings,
            collection_name="rijal"
        )

        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            temperature=0,
            max_retries=2
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """شما یک دستیار هوشمند و متخصص علم رجال شیعه هستید. 
        وظیفه شما استخراج دقیق اطلاعات راویان از متون ارائه شده است.

        متون یافت شده از دیتابیس:
        {context}

        ⚠️ قوانین تحلیل متن (بسیار مهم و حیاتی):
        ۱. 💡 درک ساختار کتاب معجم رجال: در این کتاب، هر راوی با یک شماره شروع می‌شود (مثلاً "387- أحمد بن..."). اطلاعاتِ هر راوی، فقط و فقط از جلوی نام او شروع شده و دقیقاً قبل از شروعِ شماره‌ی بعدی به پایان می‌رسد! 
        ۲. 🔴 ممنوعیت دزدی اطلاعات: به هیچ وجه جملاتِ قبل از نام راوی (که متعلق به راوی قبلی است) را نخوانید! مثلاً اگر قبل از نام راوی نوشته شده "طریقه ضعیف"، آن را به این راوی نسبت ندهید.
        ۳. 💡 درک القاب: گاهی در خطِ بعد از نام راوی، القاب او می‌آید و سپس وضعیتش (مثلاً "السيد أبو العباس: ثقة"). این "ثقه" متعلق به همان نام اصلی است که جستجو کرده‌اید.
        ۴. 🔴 ممنوعیت توهم: اگر در محدوده متنیِ اختصاصیِ همان راوی، هیچ کلمه‌ای دال بر وضعیتش (مثل ثقه، ضعیف، ممدوح) نبود، او را مطلقاً "مجهول" اعلام کنید.
        ۵. قانون تک‌راوی: اگر در ورودی فقط یک نام بود و در متن "ثقه" خوانده شده بود، بدون اما و اگر، حکم کلی سند را "صحیح" اعلام کنید.

        وظیفه شما:
        ۱. نام راوی را دقیقاً همان که کاربر داده بنویسید.
        ۲. وضعیت راوی را بر اساس کلمات متن (ثقه، ضعیف، مجهول) مشخص کنید.
        ۳. نظر علما را دقیقاً کپی کنید (اگر نبود بنویسید یافت نشد).
        ۴. حکم کلی سند را صادر کنید.
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

        for narrator in narrators:
            # جستجوی نام کامل هر راوی (مثلاً «ادريس بن عبدالله بن سعد الأشعري») به صورت واحد
            all_docs.extend(self.retriever.invoke(narrator))

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
        print(context_text[:10000] + "...\n[Truncated for display]")
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