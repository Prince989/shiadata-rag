from pydantic import BaseModel, Field
from typing import List, Optional

class SourceNode(BaseModel):
    book: str
    chapter: str
    footnotes: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceNode]
    language_detected: Optional[str] = "unknown"


class Narrator(BaseModel):
    name: str = Field(..., description="نام استخراج شده راوی")
    status: str = Field(..., description="وضعیت رجالی (مثلاً: ثقه، ضعیف، مجهول، مهمل)")
    scholars_opinion: str = Field(..., description="خلاصه نظر علمای رجال درباره این شخص")
    source: str = Field(..., description="منبع رجالی (مثلاً: رجال نجاشی، ص ۱۲۰)")

class SanadValidationResponse(BaseModel):
    overall_status: str = Field(..., description="حکم نهایی سند (صحیح، موثق، حسن، ضعیف)")
    narrators: List[Narrator] = Field(..., description="لیست تک‌تک راویان و وضعیت آن‌ها")
    detailed_analysis: str = Field(..., description="تحلیل نهایی و استدلال هوش مصنوعی")

class SanadExtractionResponse(BaseModel):
    narrators: List[str] = Field(description="لیست راویان استخراج شده و حل شده")
    matn: str = Field(description="متن خالص حدیث بدون سند")
    resolution_notes: str = Field(description="گزارش عملیات حل ضمایر")

class LifestyleItem(BaseModel):
    id: str = Field(description="شماره ردیف")
    arabic_text: str = Field(description="متن عربی حدیث")
    modern_translation: str = Field(description="ترجمه بسیار روان و امروزی به فارسی")
    lifestyle_takeaway: str = Field(description="یک پاراگراف مشاوره کاربردی و روان‌شناختی")

class LifestyleBatchResponse(BaseModel):
    advices: List[LifestyleItem] = Field(description="لیست مشاوره‌های استخراج شده برای احادیث")

class AutoTaggingResponse(BaseModel):
    seo_tags: List[str] = Field(description="آرایه‌ای از ۳ کلمه کلیدی مهم برای سئو")
    mentioned_people: List[str] = Field(description="نام افراد تاریخی ذکر شده در متن")
    domain: str = Field(description="دسته بندی اصلی متن (تاریخ، اخلاق، فقه، عقاید)")