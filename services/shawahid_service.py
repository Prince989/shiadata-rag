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
class CorroborationResponse(BaseModel):
    corroboration_status: str = Field(description="یکی از این موارد: مستفیض (شواهد متعدد)، دارای شواهد (تأیید نسبی)، غریب/منفرد (بدون شاهد)")
    supporting_chains: List[str] = Field(description="سلسله سندهای متفاوتی که همین مضمون را نقل کرده‌اند (اگر یافت شد)")
    analysis: str = Field(description="تحلیل تخصصی: آیا احادیث یافت شده، ضعف سند اصلی را جبران می‌کنند؟")

# --- Service ---
class ShawahidService:
    def __init__(self, container=None):
        from core.config import get_settings

        settings = container.settings if container else get_settings()
        self.settings = settings

        if container is not None:
            self.embeddings = container.embeddings
            # شواهد در همان دیتابیس احادیث جستجو می‌شود
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

        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=0,
            max_retries=2,
            api_key=settings.primary_google_key,
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """شما یک محدث و فقیه متخصص در شناخت «شواهد و مُتابِعات» هستید.
            وظیفه شما بررسی این است که آیا مضمون یک حدیث خاص، در احادیث دیگر با اسناد متفاوت تکرار شده است یا خیر.
            
            قوانین تحلیل:
            ۱. از آنجا که ما متن را در دیتابیس برداری جستجو کرده‌ایم، قطعاً «نفسِ همان حدیث اصلی» در بین نتایج هست. آن را نادیده بگیرید و به دنبال احادیثِ دیگر بگردید!
            ۲. بررسی کنید آیا احادیث دیگر، همان مضمون را با «سلسله راویان متفاوت» نقل کرده‌اند؟ 
            ۳. اگر مضمون با اسناد دیگر تکرار شده باشد، حدیث از حالت «غریب/منفرد» خارج شده و به دلیل وجود شواهد، ضعف سندی آن کاملاً جبران می‌شود.
            ۴. اگر احادیث یافت شده ربطی به موضوع ندارند، اعلام کنید که حدیث «منفرد/غریب» است."""),
            ("human", "حدیث اصلی (که باید برایش شاهد پیدا کنی):\n{main_hadith}\n\nاحادیث یافت شده در دیتابیس:\n{search_results}")
        ])

    def find_shawahid(self, raw_hadith: str) -> dict:
        print(f"\n🔎 [ShawahidService] Hunting for corroborating Hadiths (Shawahid)...")
        
        # جستجوی ۶ حدیث شبیه‌تر (برای اینکه اگر اولی خودش بود، ۵ تای دیگه رو بررسی کنه)
        docs = self.vectorstore.similarity_search(raw_hadith, k=6)
        
        search_results = ""
        for i, doc in enumerate(docs):
            search_results += f"--- نتیجه یافت شده {i+1} ---\n{doc.page_content}\n\n"
            
        print("   ✅ Found potential matches in Hadith DB. Sending to LLM for Shawahid analysis...")
        
        chain = self.prompt | self.llm.with_structured_output(CorroborationResponse)
        
        try:
            response_obj = chain.invoke({
                "main_hadith": raw_hadith,
                "search_results": search_results
            })
            return response_obj.model_dump()
        except Exception as e:
            print(f"❌ Shawahid LLM Error: {e}")
            raise e