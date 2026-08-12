import os
import argparse
from pipelines.ingestion_pipeline import IngestionPipeline


def batch_ingest():
    print("==================================================")
    print("📚 SHIA-DATA: SMART BATCH INGESTION ENGINE 📚")
    print("==================================================\n")

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ CRITICAL ERROR: OPENAI_API_KEY is missing!")
        return

    # تعریف فلگ‌ها (Command Line Arguments)
    parser = argparse.ArgumentParser(description="Batch Ingest EPUB and TXT books into ChromaDB")
    parser.add_argument("--force", type=str, help="Force re-ingest a specific book filename")
    parser.add_argument("--force-all", action="store_true", help="Force wipe and re-ingest ALL books")
    parser.add_argument("--collection", type=str, default="theology",
                        help="Target collection name (e.g., 'theology', 'rijal', 'hadith')")

    args = parser.parse_args()

    db_path = os.path.join("data", "chroma_db")
    epubs_dir = os.path.join("data", "raw_epubs", args.collection)

    if not os.path.exists(epubs_dir):
        print(f"❌ Error: Directory not found at {epubs_dir}")
        print(f"💡 لطفاً پوشه '{args.collection}' را در مسیر 'data/raw_epubs/' بسازید و کتاب‌ها را آنجا قرار دهید.")
        return

    # 🚀 [اصلاح بزرگ]: پیدا کردن فایل‌های EPUB و TXT به صورت همزمان
    book_files = [f for f in os.listdir(epubs_dir) if f.lower().endswith(('.epub', '.txt'))]

    if not book_files:
        print(f"⚠️ No EPUB or TXT files found in '{epubs_dir}'. Please add some books and try again.")
        return

    print(f"📂 Target Collection: [{args.collection.upper()}]")
    print(f"📁 Found {len(book_files)} books in '{epubs_dir}'. Starting batch process...\n")

    # نام کالکشن رو به پایپ‌لاین پاس می‌دیم
    pipeline = IngestionPipeline(db_directory=db_path, collection_name=args.collection)

    # حلقه روی تمام کتاب‌ها
    for filename in book_files:
        file_path = os.path.join(epubs_dir, filename)

        # تشخیص اینکه آیا باید این کتاب رو Force کنیم یا نه
        force_this_book = args.force_all or (args.force == filename)

        try:
            pipeline.run(file_path, force=force_this_book)
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {str(e)}")

    print("\n==================================================")
    print(f"✅ BATCH INGESTION TO [{args.collection.upper()}] COMPLETE!")
    print("==================================================")


if __name__ == "__main__":
    batch_ingest()