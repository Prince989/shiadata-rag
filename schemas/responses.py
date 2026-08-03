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

