from fastapi import APIRouter, HTTPException
from schemas.requests import ChatRequest
from schemas.responses import ChatResponse
from services.theology_service import TheologyService

# ساخت یک روتر (گروه‌بندی APIهای مربوط به کلام و مهدویت)
router = APIRouter()

# یک نمونه از سرویس می‌سازیم (Singleton Pattern)
theology_service = TheologyService()

@router.post("/ask", response_model=ChatResponse, summary="پاسخگویی به شبهات اعتقادی")
def ask_theology_question(request: ChatRequest):
    """
    این API یک سوال دریافت می‌کند، در دیتابیس کلامی/مهدویت جستجو کرده
    و پاسخ تحلیلی را همراه با رفرنس دقیق برمی‌گرداند.
    """
    try:
        # ارسال سوال به لایه‌ی سرویس
        response = theology_service.answer_question(request.question)
        return response
    except Exception as e:
        # اگر خطایی رخ داد، به جای کرش کردن سرور، ارور 500 استاندارد به دات‌نت می‌دهیم
        raise HTTPException(status_code=500, detail=str(e))