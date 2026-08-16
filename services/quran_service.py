import os
from pydantic import BaseModel, Field
from typing import List
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

# --- Schemas ---
class QuranValidationResponse(BaseModel):
    alignment_degree: str = Field(description="یکی از این موارد: تطابق کامل / هم‌سویی مفهومی / عدم ارتباط / تعارض صریح")
    related_ayahs: List[str] = Field(description="نام سوره، شماره آیه و متن دقیق عربی آیاتی که استناد کردید")
    analysis: str = Field(description="تحلیل دقیق و فقیهانه: آیا جزئیات حدیث در قرآن هست یا فقط مفهوم کلی آن؟")

# --- Service ---
class QuranService:
    def __init__(self, container=None):
        from core.config import get_settings

        settings = container.settings if container else get_settings()
        self.settings = settings

        if container is not None:
            self.embeddings = container.embeddings
            self.vectorstore = container.store_for("quran")
        else:
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model, api_key=settings.openai_api_key
            )
            self.vectorstore = Chroma(
                persist_directory=str(settings.chroma_dir),
                embedding_function=self.embeddings,
                collection_name="quran",
            )

        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=0,
            max_retries=2,
            api_key=settings.primary_google_key,
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """شما یک فقیه و مفسر برجسته و محتاط هستید. 
            وظیفه شما سنجش دقیق متن حدیث با آیات قرآن است (عرض الحدیث علی کتاب الله).
            
            قوانین تحلیل:
            ۱. تفاوت «مفهوم» و «جزئیات» را درک کنید. اگر قرآن می‌گوید "خودکشی حرام است" اما حدیث می‌گوید "کسی که با آهن خودکشی کند با همان آهن در جهنم می‌سوزد"، وضعیت "هم‌سویی مفهومی" است، نه "تطابق کامل" (زیرا جزئیات عذاب در قرآن نیامده).
            ۲. اگر حدیث با نص صریح یا روح آیات در تضاد است، آن را "تعارض صریح" اعلام کنید.
            ۳. حتماً متن دقیق عربی آیاتی که پیدا شده و به آن‌ها استناد می‌کنید را در خروجی بیاورید.
            ۴. تحلیل شما باید علمی، دقیق و به زبان فارسی باشد."""),
            ("human", "متن حدیث:\n{matn}\n\nآیات یافت شده در دیتابیس برای بررسی:\n{quran_context}")
        ])

    def validate_matn_with_quran(self, hadith_matn: str) -> dict:
        print(f"\n🕋 [QuranService] Searching Quran for matching concepts...")
        
        # واکشی ۵ آیه مرتبط از دیتابیس
        docs = self.vectorstore.similarity_search(hadith_matn, k=5)
        
        quran_context = ""
        for i, doc in enumerate(docs):
            quran_context += f"--- نتیجه {i+1} ---\n{doc.page_content}\n\n"
            
        print("   ✅ Found relevant Ayahs. Sending to LLM for precise Tafsir analysis...")
        
        chain = self.prompt | self.llm.with_structured_output(QuranValidationResponse)
        
        try:
            response_obj = chain.invoke({
                "matn": hadith_matn,
                "quran_context": quran_context
            })
            return response_obj.model_dump()
        except Exception as e:
            print(f"❌ Quran LLM Error: {e}")
            raise e