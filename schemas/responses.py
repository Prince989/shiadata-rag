"""
Output contracts.

Every model here serves double duty: it is the Pydantic schema handed to the
LLM for structured output *and* the FastAPI `response_model`. Keeping them as
one class is what stops the wire format and the generation schema drifting
apart -- previously the ijtihad and conflict verdicts were declared inside the
service modules and the routes had no `response_model` at all, so they were
absent from the OpenAPI document and could not be code-generated against.
"""

from typing import Any, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Chat / theology
# ---------------------------------------------------------------------------
class SourceNode(BaseModel):
    book: str
    chapter: str
    footnotes: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceNode]
    language_detected: Optional[str] = "unknown"


# ---------------------------------------------------------------------------
# Vector search
# ---------------------------------------------------------------------------
class RetrievedDocument(BaseModel):
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    distance: Optional[float] = Field(
        default=None,
        description="Raw L2 distance. LOWER IS CLOSER. Not a similarity score.",
    )
    # Promoted out of metadata for convenience; the raw dict is still included.
    book_title: Optional[str] = None
    chapter: Optional[str] = None
    domain: Optional[str] = None


class SearchResponse(BaseModel):
    collection: str
    query: str
    total_found: int
    documents: List[RetrievedDocument]


class CollectionInfo(BaseModel):
    name: str
    count: int
    metadata_keys: List[str] = Field(
        default_factory=list,
        description="Metadata keys observed in this collection, usable as filters.",
    )


# ---------------------------------------------------------------------------
# Rijal
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Lifestyle / CMS
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Ijtihad
# ---------------------------------------------------------------------------
class NarratorAnalysis(BaseModel):
    name: str = Field(description="نام راوی")
    status: str = Field(description="وضعیت رجالی (مثلاً: صحیح، موثق، ضعیف، مجهول)")


class IjtihadVerdictResponse(BaseModel):
    narrators_status: List[NarratorAnalysis] = Field(description="تحلیل تک‌تک راویان")
    sanad_status: str = Field(description="خلاصه وضعیت کل سند")
    quran_alignment: str = Field(description="وضعیت هم‌سویی با قرآن (با ذکر آیه)")
    shawahid_status: str = Field(description="وضعیت شواهد و متابعات")
    final_verdict: str = Field(description="حکم نهایی فقهی")
    detailed_reasoning: str = Field(description="استدلال جامع اصولی فقیهانه")


# ---------------------------------------------------------------------------
# Conflict resolution
# ---------------------------------------------------------------------------
class HadithSingleAnalysis(BaseModel):
    narrators: List[str] = Field(description="لیست راویان استخراج شده")
    matn: str = Field(description="متن خالص حدیث")
    sanad_status: str = Field(description="وضعیت سندی (صحیح، موثق، ضعیف، مجهول)")


class ConflictResolutionResponse(BaseModel):
    hadith_1_analysis: HadithSingleAnalysis = Field(description="تحلیل سند و متن حدیث اول")
    hadith_2_analysis: HadithSingleAnalysis = Field(description="تحلیل سند و متن حدیث دوم")
    is_conflict_detected: bool = Field(description="آیا تعارض غیرقابل جمع وجود دارد؟")
    sanad_comparison: str = Field(description="مقایسه سندی دو حدیث")
    quran_tarjih: str = Field(description="سنجش و هم‌سویی با ظاهر آیات قرآن")
    taqiyyah_analysis: str = Field(description="تحلیل احتمال تقیه (موافق یا مخالف عامه/حاکمیت وقت)")
    tarjih_rule_applied: str = Field(
        description="قاعده اصولی بکار رفته (مرجح سندی، مرجح قرآنی، حمل بر تقیه، جمع دلالی)"
    )
    final_verdict: str = Field(description="حکم نهایی فقهی")
    detailed_reasoning: str = Field(description="استدلال جامع اصولی و فقهی")


# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = Field(description="online | degraded")
    collections: dict[str, int] = Field(default_factory=dict)
    rijal_index_size: Optional[int] = None
    degraded: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Storyteller (left in place; the route is unchanged and still broken by design
# until the NestJS storyteller replaces it -- see the plan.)
# ---------------------------------------------------------------------------
class StoryStepResponse(BaseModel):
    narrative_text: str = Field(description="پاراگراف جدید داستان")
    image_prompt: str = Field(description="پرامپت انگلیسی تولید شده")
    image_url: Optional[str] = Field(default=None, description="لینک تصویر تولید شده")
    sources: List[str] = Field(description="منابع تاریخی")
