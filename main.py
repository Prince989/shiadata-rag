from pipelines.retrieval_pipeline import RetrievalPipeline
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from schemas.responses import ChatResponse
from api.routes import theology, rijal, hadith

# راه‌اندازی اپلیکیشن FastAPI با مستندات خودکار
app = FastAPI(
    title="SHIA-DATA AI Engine",
    description="Enterprise-Grade Islamic AI API for .NET CMS",
    version="1.0.0",
    docs_url="/docs",     # آدرس پنل Swagger
    redoc_url="/redoc"    # آدرس پنل ReDoc
)

# تنظیمات CORS (برای اینکه پروژه‌ی دات‌نت یا Next.js بتونه بدون خطای امنیتی بهش وصل بشه)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در پروداکشن اینجا آدرس دامنه guided-one رو می‌ذاریم
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# یک Route ساده برای تست زنده بودن سرور (Health Check)
@app.get("/api/v1/health", tags=["System"])
def health_check():
    return {
        "status": "online",
        "message": "🧠 SHIA-DATA AI Engine is up and running!"
    }

# ثبت کردن API کلام و مهدویت در سرور اصلی
app.include_router(
    theology.router,
    prefix="/api/v1/theology",
    tags=["Theology & Mahdawiyyat"]
)

app.include_router(rijal.router, prefix="/api/v1/rijal", tags=["Ilm al-Rijal (Hadith Validation)"])
app.include_router(hadith.router)

@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
def chat_with_bot():
    print("==================================================")
    print("🧠 SHIA-DATA AI ENGINE IS ONLINE (Type 'exit' to quit)")
    print("==================================================\n")

    # روشن کردن موتورِ جستجو
    pipeline = RetrievalPipeline()

    while True:
        question = input("\n👤 You: ")
        if question.lower() in ['exit', 'quit']:
            print("👋 Goodbye!")
            break

        if not question.strip():
            continue

        print("\n🤖 AI is thinking...\n")
        answer = pipeline.ask(question)
        print("--------------------------------------------------")
        print(f"💡 AI Answer:\n{answer}")
        print("--------------------------------------------------")


if __name__ == "__main__":
    print("==================================================")
    print("🚀 Starting SHIA-DATA API Server...")
    print("🌐 Swagger Docs available at: http://localhost:8000/docs")
    print("==================================================")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

'''
if __name__ == "__main__":
    chat_with_bot()
'''
