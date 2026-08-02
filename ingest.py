import os
from pipelines.ingestion_pipeline import IngestionPipeline

def ingest_book():
    print("==================================================")
    print("📚 SHIA-DATA: SMART BOOK INGESTION ENGINE 📚")
    print("==================================================\n")

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ CRITICAL ERROR: OPENAI_API_KEY is missing!")
        return

    db_path = os.path.join("data", "chroma_db")

    # اسم فایل کتابی که می‌خوای الان اضافه کنی رو اینجا بنویس
    # می‌تونی به "al-ghayba.epub" تغییرش بدی
    epub_filename = "Kitab al-Ghayba_ The Book of Occultation.epub"
    epub_path = os.path.join("data", "raw_epubs", epub_filename)

    if not os.path.exists(epub_path):
        print(f"❌ Error: File not found at {epub_path}")
        return

    try:
        pipeline = IngestionPipeline(db_directory=db_path)
        pipeline.run(epub_path)
    except Exception as e:
        print(f"\n❌ Pipeline failed due to an error: {str(e)}")


if __name__ == "__main__":
    ingest_book()