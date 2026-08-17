import json
import os
import sys
from pathlib import Path

# Allow `python scripts/ingest_quran.py` from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

from core.paths import CHROMA_DIR, QURAN_JSON_PATH

load_dotenv()

def ingest_quran(json_path: str = str(QURAN_JSON_PATH), db_directory: str = str(CHROMA_DIR)):
    print("\n" + "="*50)
    print("📖 STARTING QURAN INGESTION ENGINE 📖")
    print("="*50)

    if not os.path.exists(json_path):
        print(f"❌ Error: Could not find {json_path}")
        return

    # 1. خواندن فایل JSON
    with open(json_path, "r", encoding="utf-8") as f:
        quran_data = json.load(f)

    print(f"✅ Loaded {len(quran_data)} Ayahs from JSON.")

    # 2. تبدیل به داکیومنت‌های Langchain
    documents = []
    for ayah in quran_data:
        # متادیتا برای فیلتر کردن دقیق (مثلاً فقط جستجو در سوره بقره)
        metadata = {
            "surah_number": ayah["surah_number"],
            "surah_name_ar": ayah["surah_name_ar"],
            "surah_name_en": ayah["surah_name_en"],
            "ayah_number": ayah["ayah_number"]
        }
        
        doc = Document(page_content=ayah["searchable_text"], metadata=metadata)
        documents.append(doc)

    # 3. راه‌اندازی دیتابیس برداری
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        persist_directory=db_directory,
        embedding_function=embeddings,
        collection_name="quran"  # 👈 کالکشن اختصاصی قرآن
    )

    # 4. تزریق به صورت دسته‌ای (Batch Processing) برای جلوگیری از Timeout
    batch_size = 500
    total_batches = (len(documents) // batch_size) + 1

    print(f"🚀 Starting embedding process in {total_batches} batches...")
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        current_batch = (i // batch_size) + 1
        print(f"   ⏳ Processing Batch {current_batch}/{total_batches} ({len(batch)} Ayahs)...")
        vectorstore.add_documents(documents=batch)

    print("🎉 SUCCESS! The Holy Quran is fully ingested and ready for Semantic Search.")

if __name__ == "__main__":
    ingest_quran()