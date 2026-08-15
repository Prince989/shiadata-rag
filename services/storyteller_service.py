import os
import base64
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings 
from openai import OpenAI

from services.llm_gateway import LLMGateway # 👈 تغییر حیاتی اینجاست

class StorytellerService:
    def __init__(self, db_directory: str = "./data/chroma_db"):
        self.llm_writer = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.7)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # حالا این کلاینت واقعی DALL-E است
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.gateway = LLMGateway()
        self.vectorstore = Chroma(
            persist_directory=db_directory,
            embedding_function=self.embeddings,
            collection_name="hadith"
        )

    def search_similar_hadiths(self, query: str, top_k: int = 3, domain_filter: str = None):
        search_kwargs = {"k": top_k}
        if domain_filter:
            search_kwargs["filter"] = {"domain": domain_filter}

        # 💡 تغییر اول: کل داکیومنت‌ها رو برمی‌گردونیم تا متادیتا (منابع) حفظ بشه
        docs = self.vectorstore.similarity_search(query, **search_kwargs)
        return docs
    
    def generate_next_step(self, topic: str, previous_context: str, user_prompt: str) -> dict:
        search_query = f"{topic} {user_prompt}"
        rag_docs = self.search_similar_hadiths(search_query, top_k=5, domain_filter="history")   
        
        historical_facts = "\n\n".join([doc.page_content for doc in rag_docs])
        
        # ----- ۱. تولید متن داستان -----
        writer_prompt = f"""شما یک قصه‌گوی چیره‌دست و امانت‌دار تاریخ اسلام هستید.
        موضوع کلی: {topic}
        آنچه تا الان گذشته: {previous_context}
        فکت‌های تاریخی جدید یافت شده: {historical_facts}
        درخواست کاربر برای ادامه: {user_prompt}
        
        وظیفه: فقط یک پاراگراف جذاب، دراماتیک و تصویرساز به زبان فارسی بنویسید که داستان را جلو ببرد."""
        
        # writer_response = self.llm_writer.invoke(writer_prompt)
        try:
            writer_response = self.gateway.invoke_structured(
                prompt=writer_prompt
            )
            writer_response = writer_response.model_dump()
        except Exception as e:
            print(f"❌ Conflict Resolver Gateway Error: {e}")
            raise e
        
        if isinstance(writer_response.content, list):
            narrative_text = "".join([str(item.get("text", "")) for item in writer_response.content if item.get("type") == "text"])
        else:
            narrative_text = str(writer_response.content)

        # ----- ۲. تولید پرامپت عکس -----
        director_prompt = f"""Translate this Persian story scene into a highly detailed, cinematic English prompt for image generation. 
        Focus on lighting, characters (without showing faces of holy figures), environment, and mood.
        Scene: {narrative_text}"""
        
        # director_response = self.llm_writer.invoke(director_prompt)
        try:
            director_response = self.gateway.invoke_structured(
                prompt=director_prompt
            )
            director_response = director_response.model_dump()
        except Exception as e:
            print(f"❌ Conflict Resolver Gateway Error: {e}")
            raise e
        
        if isinstance(director_response.content, list):
            image_prompt_str = "".join([str(item.get("text", "")) for item in director_response.content if item.get("type") == "text"])
        else:
            image_prompt_str = str(director_response.content)
            
        # (خط اضافه و مخرب از اینجا پاک شد)

        # ----- ۳. تولید عکس با OpenAI -----
        image_url = None
        try:
            # ارسال رشته متنی خالص (image_prompt_str) به OpenAI
            response = self.client.responses.create(
                model="gpt-5.6",
                input=image_prompt_str, 
                tools=[{"type": "image_generation"}],
            )
            
            image_data = [
                output.result
                for output in response.output
                if output.type == "image_generation_call"
            ]
            
            if image_data:
                image_base64 = image_data[0]
                image_path = "temp_story_image.png"
                with open(image_path, "wb") as f:
                    f.write(base64.b64decode(image_base64))
                image_url = image_path
                
        except Exception as e:
            print(f"⚠️ Image generation failed or was skipped: {e}")
            image_url = None

        # ----- ۴. استخراج منابع -----
        extracted_sources = []
        for doc in rag_docs:
            source_name = doc.metadata.get("book_title", "منبع نامشخص")
            if source_name not in extracted_sources:
                extracted_sources.append(source_name)
        
        return {
            "narrative_text": narrative_text,
            "image_prompt": image_prompt_str,
            "image_url": image_url, 
            "sources": extracted_sources
        }