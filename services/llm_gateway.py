import os
from litellm import Router
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class LLMGateway:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMGateway, cls).__new__(cls)
            cls._instance._initialize_router()
        return cls._instance

    def _initialize_router(self):
        print("🌐 [LLMGateway] Initializing Pure LiteLLM Router with Direct API Keys...")
        
        # استخراج کلیدهای مستقیم گوگل از فایل .env
        keys = [os.getenv(f"GOOGLE_API_KEY{i}") for i in range(1, 11) if os.getenv(f"GOOGLE_API_KEY{i}")]
        
        if not keys:
            raise ValueError("❌ هیچ کلیدی با فرمت GEMINI_API_KEY_X در فایل .env یافت نشد!")

        print(f"   ✅ {len(keys)} API Keys detected. Setting up Round-Robin.")

        # ساخت لیست مدل‌ها برای چرخش ترافیک
        model_list = []
        for key in keys:
            model_list.append({
                "model_name": "gemini-3.5-flash", 
                "litellm_params": {
                    "model": "gemini/gemini-3.5-flash", # اتصال مستقیم به سرورهای گوگل
                    "api_key": key
                }
            })

        # راه‌اندازی روتر چرخان
        self.router = Router(
            model_list=model_list,
            routing_strategy="simple-shuffle", 
            num_retries=2,                  
            allowed_fails=1                 
        )

    def invoke_structured(self, prompt: str, schema_class: type[BaseModel]) -> BaseModel:
        """
        ارسال پرامپت به روتر چرخشی و دریافت خروجی Pydantic
        """
        response = self.router.completion(
            model="gemini-3.5-flash",
            messages=[{"role": "user", "content": prompt}],
            response_format=schema_class 
        )
        
        raw_json = response.choices[0].message.content
        return schema_class.model_validate_json(raw_json)