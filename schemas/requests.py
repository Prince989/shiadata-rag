"""Input contracts."""

from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

CollectionName = Literal["theology", "hadith", "rijal", "quran"]

# Metadata values across all four collections are scalar (see the domain,
# language, has_sanad, volume, surah_number, ... keys in core/catalog.json and
# the ingestion pipelines). Restricting to scalars means a malformed filter
# value -- e.g. an empty object, which is what Swagger's "Try it out" example
# fills in for a bare dict[str, Any] -- is rejected with a 422 here, instead
# of reaching Chroma and failing with "Expected operator expression to have
# exactly one operator, got {} in query."
FilterValue = Union[str, int, bool]


class ChatRequest(BaseModel):
    question: str = Field(
        ..., min_length=1, max_length=8_000,
        description="سوال کاربر به هر زبانی (فارسی، عربی، انگلیسی)",
    )
    collection: CollectionName = Field(
        default="theology", description="کالکشنی که باید در آن جستجو شود"
    )
    top_k: int = Field(default=7, ge=1, le=20, description="تعداد قطعات بازیابی‌شده")


class SanadValidationRequest(BaseModel):
    sanad_text: list[str] = Field(
        ...,
        min_length=1,
        description="لیست نام راویان (نه یک رشته‌ی واحد). خروجی /hadith/extract-sanad",
    )


class VectorSearchRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "خلق السماوات و الارض",
                "collection": "hadith",
                "top_k": 5,
                "filters": {"domain": "history"},
                "search_type": "similarity",
                "fetch_k": 30,
                "lambda_mult": 0.5,
                "include_distances": True,
            }
        }
    )

    query: str = Field(..., min_length=1, max_length=8_000)
    collection: CollectionName = "hadith"
    top_k: int = Field(default=5, ge=1, le=50)
    filters: Optional[dict[str, FilterValue]] = Field(
        default=None,
        description='فیلتر متادیتا با مقادیر ساده (رشته/عدد/بولین)، مثلاً {"domain": "history"}. چند کلید با $and ترکیب می‌شود.',
    )
    search_type: Literal["similarity", "mmr"] = "similarity"
    fetch_k: int = Field(default=30, ge=1, le=200, description="فقط برای mmr")
    lambda_mult: float = Field(default=0.5, ge=0.0, le=1.0, description="فقط برای mmr")
    include_distances: bool = True


class StoryStepRequest(BaseModel):
    topic: str = Field(..., description="موضوع اصلی داستان (مثلاً: جنگ خندق)")
    previous_context: Optional[str] = Field(
        default="", description="پاراگراف‌های قبلی داستان برای حفظ پیوستگی"
    )
    user_prompt: Optional[str] = Field(
        default="ادامه داستان را بگو", description="انتخاب کاربر برای مسیر بعدی قصه"
    )
