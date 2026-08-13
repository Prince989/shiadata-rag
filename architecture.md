# 🏛️ SHIA-DATA AI ENGINE: Architecture & Master Plan

## 📌 1. Project Vision
SHIA-DATA is an Enterprise-Grade, Data-Driven Islamic AI Engine. It is not just a chatbot, but a comprehensive Microservices Architecture built with **FastAPI**. It serves as the intelligent backbone for .NET CMS platforms, offering services ranging from theological analysis and Rijal validation to automated content creation and AI media generation.

## 🛠️ 2. Tech Stack
- **Framework:** FastAPI (Python)
- **AI Core:** LangChain, OpenAI (GPT-4o-mini for reasoning, DALL-E 3 for image generation)
- **Vector Database:** ChromaDB (Multi-Collection Architecture)
- **Data Validation:** Pydantic

## 📂 3. Directory Structure (Clean/Layered Architecture)
This structure MUST be strictly followed for any new developments to prevent technical debt and ensure scalability:

```text
AIEngine/
 ├── main.py                  # Entry point: FastAPI server setup, CORS, and Middlewares
 │
 ├── api/                     # UI/Routing Layer (Only handles HTTP requests/responses)
 │    ├── routes/
 │    │    ├── chat.py        # Agentic Chatbot (Routes intents to specific tools)
 │    │    ├── rijal.py       # Rijal & Sanad validation APIs
 │    │    ├── hadith.py      # Hadith sourcing, conflict resolution, and analysis
 │    │    ├── theology.py    # Theological Q&A and Mahdawiyyat
 │    │    ├── tafsir.py      # Tafsir Quran
 │    │    ├── cms.py         # CMS Tools: Auto-tagging, Summarization, Recommendations
 │    │    └── media.py       # Image Generation (DALL-E 3) & Future TTS
 │    └── dependencies.py     # Auth, API Key validation, and shared deps
 │
 ├── services/                # Business Logic Layer (Heavy lifting happens here)
 │    ├── agent_service.py    # LLM Router and Tool-calling logic
 │    ├── rijal_service.py    # Database querying for Rijal rules
 │    ├── content_service.py  # Summarization and NLP logics
 │    └── media_service.py    # Communication with DALL-E 3
 │
 ├── core/                    # Core Infrastructure
 │    ├── databases/          # ChromaDB connection & Multi-Collection Management
 │    ├── prompts/            # Centralized System Prompts (English strictly)
 │    └── tools/              # Tools accessible by the Agent (e.g., search_rijal, generate_image)
 │
 ├── schemas/                 # Data Validation Layer (Pydantic)
 │    ├── requests.py         # Input JSON structures expected from .NET
 │    └── responses.py        # Output JSON structures sent to .NET
 │
 ├── data/
 │    ├── raw_epubs/          # Raw books for ingestion
 │    └── chroma_db/          # Local Vector Database
 │
 ├── ingest.py                # Idempotent batch processing CLI
 ├── .env                     # Environment variables
 └── requirements.txt         # Direct dependencies only
 
```

## 🚀 4. Core Microservices & Features
A. The Agentic Chatbot (chat.py)
Super Assistant: Uses LLM routing (Agent) to detect the user's intent.

Tool Calling: It can dynamically switch between searching the Theology DB, validating a Hadith in the Rijal DB, or calling DALL-E to generate an image based on the chat context.

### B. Hadith & Rijal Lab (rijal.py, hadith.py)
Validate Sanad: Extracts narrator chains and cross-references them with classical Rijal databases to determine authenticity (Thiqah, Da'if, etc.).

Track Sources (Takhrij): Finds exact or semantic matches of a hadith text within the major collections (Kutub al-Arba'a, Bihar, etc.).

Resolve Conflicts: Analyzes contradictory Ahadith using Shuruh (commentaries).

### C. CMS Toolkit (cms.py)
Auto-Tagging: Extracts SEO tags, categories, and keywords from raw text.

Entity Extraction: Identifies People, Places, and Books to build relational graphs.

Summarization: Creates concise excerpts for UI display.

Semantic Recommendations: Suggests related articles based on vector similarity.

### D. Media Engine (media.py)
AI Image Generation: Integrates with DALL-E 3. Translates concepts/articles/ahadith into optimized English prompts to generate high-quality UI/Social Media images for the CMS.

### E. Multi-Collection DB Engine (core/databases/)
Data is strictly segregated into collections to avoid contextual hallucination:

Collection_Theology (Mahdawiyyat, Kalam)

Collection_Rijal (Biographical data of narrators)

Collection_Hadith (Raw narrations for sourcing)

## ⚠️ 5. AI Developer Instructions (For Future Prompts)
When a human developer asks you (the AI) to build a new feature:

Always read this architecture first.

Do not mix layers: Routes must go in api/routes/, logic in services/, and schemas in schemas/.

Pydantic First: Always define Input/Output models in schemas/ before writing route logic.

No Hallucination: The RAG system must strictly use the Fallback prompt if data is missing from ChromaDB.


## 6. Future Features 

۱. قصه‌گوی تعاملی و مصور (Interactive Visual Storyteller)دقیقاً همون ایده‌ای که دیدی، ولی با قدرتِ تولید در لحظه (Real-time).چطور کار می‌کنه: کاربر موضوعی رو انتخاب می‌کنه (مثلاً جنگ خندق). رباتِ ما (chat.py) با استفاده از دیتابیس کلام و تاریخ (Collection_Theology) داستان رو مرحله به مرحله برای کاربر تعریف می‌کنه.  جادوی سیستم: همزمان با تولید هر پاراگراف از داستان، موتور رسانه (media.py) یک پرامپت انگلیسی بهینه می‌سازه و از DALL-E 3 یک تصویرسازیِ باکیفیت برای اون صحنه دریافت می‌کنه. کاربر احساس می‌کنه داره یک کمیک‌بوک یا بازیِ داستان‌محور رو تجربه می‌کنه، نه اینکه فقط یک مقاله خشک بخونه.  ۲. مشاورِ هوشمند سبک زندگی (Lifestyle AI Companion)کاربر عادی نمیاد سرچ کنه "احادیث بابِ غیبت". کاربر عادی مشکلِ روزمره داره.چطور کار می‌کنه: همون ربات هوشمند ما (chat.py) که الان می‌تونه شبهات رو با مسیریابی به دیتابیس‌ها جواب بده، می‌تونه نقش مشاور رو بازی کنه. کاربر می‌پرسه: "امروز خیلی ناامیدم، حس می‌کنم همه‌چی قفل شده".  جادوی سیستم: سیستم با استفاده از دیتابیس خام روایات (Collection_Hadith)، روایاتی درباره امید و توکل پیدا می‌کنه. سپس LLM اون حدیث رو از حالتِ خشکِ عربی خارج می‌کنه و به شکل یک دیالوگِ گرم، روان و انگیزشی به کاربر ارائه می‌ده.  ۳. کارخانه‌ی تولید اینفوگرافیک و محتوای شبکه‌های اجتماعییکی از نیازهای بزرگ افراد مذهبی، پیدا کردن محتوای شیک برای استوری اینستاگرام یا کانال‌هاست.چطور کار می‌کنه: ما در ابزارهای سیستم مدیریت محتوا (cms.py) قابلیت خلاصه‌سازی متون (Summarization) رو داریم.  جادوی سیستم: کاربر یک متن طولانی مذهبی یا یک خطبه رو به سیستم می‌ده. لایه‌ی CMS اون رو به چند جمله‌ی کوتاه و کوبنده خلاصه می‌کنه. سپس media.py با DALL-E 3 یک تصویر پس‌زمینه برای اون محتوا می‌سازه. در نهایت، بک‌اندِ ما می‌تونه این خروجی رو به فرانت‌اندِ .NET پاس بده تا یک پستِ شبکه‌ی اجتماعیِ آماده تحویل کاربر بشه.  ۴. گرافِ دانشِ بصری (The Islamic Knowledge Graph)یادگیری بصری برای کاربر عام خیلی جذاب‌تر از خوندنِ لیسته.چطور کار می‌کنه: ما در cms.py قابلیت استخراج موجودیت‌ها (Entity Extraction) رو تعبیه کردیم که می‌تونه افراد، مکان‌ها و کتاب‌ها رو تشخیص بده تا گراف‌های رابطه‌ای بسازه.  جادوی سیستم: با این قابلیت می‌تونیم تو سایت یک "ویکی‌پدیای بصری" بسازیم. کاربر روی اسم «مختار» کلیک می‌کنه و سیستم به صورت گرافیکی و شبکه‌ای نشون می‌ده که او با چه کسانی در ارتباط بوده، در چه جنگ‌هایی شرکت کرده و نامش در چه کتاب‌هایی آمده است.


https://share.gemini.google/RiPdxzm7amSW