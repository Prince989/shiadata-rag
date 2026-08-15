from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from schemas.responses import SanadValidationResponse
from dotenv import load_dotenv
import os
import re

load_dotenv()


class RijalService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = Chroma(
            persist_directory="./data/chroma_db",
            embedding_function=self.embeddings,
            collection_name="rijal"
        )
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 20, "fetch_k": 50, "lambda_mult": 0.5}
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
        ۵. درک فرمت‌های اختصاصی: در برخی متون، وضعیت راوی مستقیماً بعد از علامت مساوی (=) نوشته شده است.
        ۶. 💡 تفکیک ضعف راوی از ضعف طریق (بسیار مهم): اگر در کانتکست بعد از علامت مساوی نوشته شده بود «= ضعيف بـ...» (مثلاً: = ضعيف بأبي المفضل وابن بطة، یا ضعيف بأحمد بن محمد)، این یعنی «طریقِ شیخ به کتابِ آن راوی ضعیف است»، نه اینکه خودِ شخصِ راوی ضعیف باشد! در این حالت حق ندارید راوی را "ضعیف" معرفی کنید. وضعیت او را "مجهول (با طریق ضعیف)" درج کنید و در بخش نظرات علما صراحتاً بنویسید که ضعف فقط مربوط به طریق است نه شخص.
        ۷. تجمیع منابع: اگر اطلاعات یک راوی در چندین منبع تکرار شده، نام و آدرس دقیق تمام آن منابع را در بخش source درج کنید.

        وظیفه شما:
        ۱. نام راوی.
        ۲. وضعیت راوی (ثقه، ضعیف، مجهول، مجهول (با طریق ضعیف)، صحیح).
        ۳. نظر علما (کپی دقیق از کانتکست).
        ۴. حکم کلی سند.
        """),
            ("human", "سند برای بررسی: {sanad}")
        ])

    # 🚀 اصلاح بزرگ: دریافت لیست راویان به جای استرینگ خام
    def validate_sanad(self, narrators: list[str]) -> dict:
        print(f"\n🔍 [RijalService] Analyzing Narrators List: {narrators}")

        all_docs = []
        print("   📥 Fetching entire Vector DB for exact memory match...")
        all_db_data = self.vectorstore.get(include=["documents", "metadatas"])

        for narrator in narrators:
            narrator_clean = narrator.strip()

            n_fa = narrator_clean.replace("ي", "ی").replace("ك", "ک").replace("أ", "ا")
            n_ar = narrator_clean.replace("ی", "ي").replace("ک", "ك").replace("ا", "أ")

            print(f"   🔍 Memory Hunting for: '{narrator_clean}'")

            exact_matches = []
            from langchain_core.documents import Document

            for text, meta in zip(all_db_data["documents"], all_db_data["metadatas"]):
                if narrator_clean in text or n_fa in text or n_ar in text:
                    exact_matches.append(Document(page_content=text, metadata=meta))

            if exact_matches:
                print(f"      ✅ BINGO! Found {len(exact_matches)} exact matches.")

                def score_doc(doc):
                    text = doc.page_content
                    score = 0
                    if re.search(r'(^|\n|\-)\s*' + re.escape(narrator_clean), text):
                        score += 100
                    if re.search(r'(^|\n|\-)\s*' + re.escape(n_ar), text):
                        score += 100
                    if any(word in text for word in ["=", "ضعيف", "ثقة", "ثقه", "صحيح", "مجهول"]):
                        score += 50
                    score -= len(text) / 1000
                    return score

                exact_matches.sort(key=score_doc, reverse=True)
                all_docs.extend(exact_matches[:5])
            else:
                print(f"      ⚠️ No exact match anywhere. Falling back to Vector Search...")
                all_docs.extend(self.retriever.invoke(narrator_clean))

        unique_pages = set()
        context_text = ""

        for doc in all_docs:
            page_ref = doc.metadata.get('chapter', 'Unknown Page')
            if page_ref not in unique_pages:
                unique_pages.add(page_ref)
                chunk_text = doc.page_content.strip()
                if chunk_text and len(chunk_text) > 20:
                    context_text += f"--- منبع ({doc.metadata.get('book_title')} - {page_ref}) ---\n{chunk_text}\n\n"

        if not context_text:
            context_text = "هیچ متنی در دیتابیس یافت نشد."

        print("🤖 Step 3: Synthesizing AI Verdict...")
        chain = self.prompt | self.llm.with_structured_output(SanadValidationResponse)

        try:
            # ارسال نام راویان به صورت یک رشته با کاما برای قاضی نهایی
            sanad_string = "، ".join(narrators)
            response_obj = chain.invoke({"context": context_text, "sanad": sanad_string})
            return response_obj.model_dump()
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            raise e