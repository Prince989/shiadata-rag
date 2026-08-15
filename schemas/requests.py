from typing import Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field(..., description="سوال کاربر به هر زبانی (فارسی، عربی، انگلیسی)")
    # در آینده می‌تونیم پارامترهایی مثل user_id یا session_id رو هم اینجا اضافه کنیم

class SanadValidationRequest(BaseModel):
    sanad_text: str = Field(..., description="متن عربی سند حدیث (مثال: عن فلان عن فلان...)")

class StoryStepRequest(BaseModel):
    topic: str = Field(..., description="موضوع اصلی داستان (مثلاً: جنگ خندق)")
    previous_context: Optional[str] = Field(default="", description="پاراگراف‌های قبلی داستان برای حفظ پیوستگی")
    user_prompt: Optional[str] = Field(default="ادامه داستان را بگو", description="انتخاب کاربر برای مسیر بعدی قصه")