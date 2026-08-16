import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings

from core.config import get_settings
from schemas.responses import SanadExtractionResponse, LifestyleBatchResponse, AutoTaggingResponse

logger = logging.getLogger(__name__)


class HadithService:
    def __init__(self, container=None):
        settings = container.settings if container else get_settings()
        self.settings = settings

        # api_key is passed explicitly. This used to read GEMINI_API_KEY, which
        # is defined nowhere -- it only worked because langchain-google-genai
        # falls back to GOOGLE_API_KEY and an earlier import happened to have
        # called load_dotenv() first.
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=0,
            api_key=settings.primary_google_key,
        )

        if container is not None:
            self.embeddings = container.embeddings
            self.vectorstore = container.store_for("hadith")
        else:
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model, api_key=settings.openai_api_key
            )
            self.vectorstore = Chroma(
                persist_directory=str(settings.chroma_dir),
                embedding_function=self.embeddings,
                collection_name="hadith",
            )

    # ==========================================
    # فیچر ۱: جراحی سند و متن (Sanad Extraction)
    # ==========================================
    def extract_sanad(self, raw_text: str) -> SanadExtractionResponse:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """شما یک متخصص برجسته علم رجال، حدیث‌شناسی شیعه و پردازش زبان طبیعی هستید.
وظیفه شما کالبدشکافی احادیث و استخراج دقیق «سلسله راویان» (سند) و جدا کردن آن از «متن حدیث» است.
۱. سند را از متن اصلی جدا کنید.
۲. حل ضمایر: این مهم‌ترین وظیفه شماست. ضمایری مانند "عن أبيه" را بر اساس راوی قبلی حل کنید.
۳. کلماتی مانند "عن"، "حدثنا" و "قال" را حذف کنید."""),
            ("human", "این حدیث را کالبدشکافی کن:\n{text}")
        ])

        # جادوی LangChain: تحمیل Pydantic به خروجی جمینای
        structured_llm = self.llm.with_structured_output(SanadExtractionResponse)
        chain = prompt | structured_llm

        return chain.invoke({"text": raw_text})

    # ==========================================
    # فیچر ۲: مشاور سبک زندگی (Lifestyle Advice)
    # ==========================================
    def generate_lifestyle_advice(self, hadiths_list: list[str]) -> LifestyleBatchResponse:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """شما یک مشاور سبک زندگی اسلامی و متخصص پردازش داده هستید.
من به شما چندین حدیث می‌دهم. شما به هیچ وجه نباید آن‌ها را با هم ترکیب یا خلاصه‌سازی کنید.
برای تک‌تک احادیث به صورت کاملاً مجزا، تحلیل روان‌شناختی و کاربردی ارائه دهید."""),
            ("human", "احادیث زیر را تحلیل کن:\n{texts}")
        ])

        structured_llm = self.llm.with_structured_output(LifestyleBatchResponse)
        chain = prompt | structured_llm

        joined_texts = "\n\n".join([f"حدیث {i + 1}: {h}" for i, h in enumerate(hadiths_list)])
        return chain.invoke({"texts": joined_texts})

    # ==========================================
    # فیچر ۳: استخراج موجودیت برای گراف دانش
    # ==========================================
    def auto_tag_document(self, historical_text: str) -> AutoTaggingResponse:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """شما یک سیستم هوشمند استخراج موجودیت (Entity Extraction) هستید.
متن تاریخی ورودی را بخوانید و کلمات کلیدی سئو، نام افراد تاریخی و دامین کلی متن را استخراج کنید."""),
            ("human", "متن:\n{text}")
        ])

        structured_llm = self.llm.with_structured_output(AutoTaggingResponse)
        chain = prompt | structured_llm

        return chain.invoke({"text": historical_text})

    # ==========================================
    # متد کمکی: جستجوی برداری (Vector Search)
    # ==========================================
    def search_similar_hadiths(
        self, query: str, top_k: int = 3, domain_filter: str = None
    ) -> list[Document]:
        """
        Returns full Documents, not bare strings.

        This previously returned [doc.page_content ...], discarding book_title,
        chapter and domain. Without that metadata no caller can cite a source,
        which blocks citation rendering entirely downstream.
        """
        search_kwargs = {"k": top_k}
        if domain_filter:
            search_kwargs["filter"] = {"domain": domain_filter}

        return self.vectorstore.similarity_search(query, **search_kwargs)