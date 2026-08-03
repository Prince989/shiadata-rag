from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field(..., description="سوال کاربر به هر زبانی (فارسی، عربی، انگلیسی)")
    # در آینده می‌تونیم پارامترهایی مثل user_id یا session_id رو هم اینجا اضافه کنیم

class SanadValidationRequest(BaseModel):
    sanad_text: str = Field(..., description="متن عربی سند حدیث (مثال: عن فلان عن فلان...)")