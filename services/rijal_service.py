from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from schemas.responses import SanadValidationResponse


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
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """شما یک مجتهد و متخصص علم رجال شیعه هستید. 
با استفاده از متون رجالی زیر، وضعیت راویان موجود در سند را تحلیل کنید.

متون یافت شده از دیتابیس:
{context}

⚠️ قوانین رجالی (مهم):
۱. انحراف مذهبی (مثل واقفی بودن) لزوماً به معنای «ضعیف» بودن نیست. اگر راوی توثیق شده باشد (ثقه)، او معتبر است.
۲. اگر در متن صراحتاً نجاشی، شیخ طوسی یا آیت‌الله خویی او را «ثقه» یا «مورد اعتماد» خوانده‌اند، او را ثقه اعلام کنید.
۳. اگر درباره راوی هیچ مدح و ذمی در متون یافت نشد، او را "مجهول" اعلام کن.
۴. قانون طلایی سند: اگر حتی یک راویِ ضعیف یا مجهول در سلسله سند باشد، حکم کلی سند "ضعیف" می‌شود.

وظیفه شما:
۱. وضعیت تک‌تک راویان را مشخص کنید.
۲. نظر علما را دقیقاً بر اساس متن بنویسید.
۳. حکم کلی سند را صادر کنید.
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
        print(context_text[:1000] + "...\n[Truncated for display]")
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