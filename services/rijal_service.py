import logging
import re

from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate

from core.config import get_settings
from schemas.responses import SanadValidationResponse

logger = logging.getLogger(__name__)


class RijalService:
    def __init__(self, container=None):
        settings = container.settings if container else get_settings()
        self.settings = settings
        self.container = container

        if container is not None:
            self.embeddings = container.embeddings
            self.vectorstore = container.store_for("rijal")
        else:
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model, api_key=settings.openai_api_key
            )
            self.vectorstore = Chroma(
                persist_directory=str(settings.chroma_dir),
                embedding_function=self.embeddings,
                collection_name="rijal",
            )

        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 20, "fetch_k": 50, "lambda_mult": 0.5}
        )
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=0,
            max_retries=2,
            api_key=settings.primary_google_key,
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

    def validate_sanad(self, narrators: list[str]) -> dict:
        logger.info("analyzing narrators: %s", narrators)

        all_docs = []
        index = self.container.rijal_index if self.container else None

        for narrator in narrators:
            narrator_clean = narrator.strip()

            if index is not None:
                # Normalized substring match against an index built once at
                # startup, instead of dumping and scanning the full 12,941-doc
                # collection on every call.
                exact_matches = index.lookup(narrator_clean, limit=5)
            else:
                exact_matches = []

            if exact_matches:
                logger.info(
                    "'%s': %d exact matches", narrator_clean, len(exact_matches)
                )
                all_docs.extend(exact_matches)
            else:
                logger.info(
                    "'%s': no exact match, falling back to vector search",
                    narrator_clean,
                )
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

        logger.info("synthesizing AI verdict")
        chain = self.prompt | self.llm.with_structured_output(SanadValidationResponse)

        try:
            sanad_string = "، ".join(narrators)
            response_obj = chain.invoke({"context": context_text, "sanad": sanad_string})
            return response_obj.model_dump()
        except Exception as e:
            logger.error("LLM error in validate_sanad: %s", e)
            raise