from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


def xray_database():
    print("==================================================")
    print("🔍 SHIA-DATA: DATABASE X-RAY 🔍")
    print("==================================================\n")

    # اتصال به دیتابیس بدون هیچ فیلتری
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    db = Chroma(persist_directory="./data/chroma_db", embedding_function=embeddings)

    # واکشی تمام دیتای موجود (بدون سرچ معنایی)
    all_data = db.get()
    metadatas = all_data.get('metadatas', [])

    if not metadatas:
        print("❌ Database is completely empty!")
        return

    # شمارش تعداد چانک‌ها به تفکیک نام کتاب
    book_counts = {}
    for meta in metadatas:
        title = meta.get('book_title', 'Unknown Book')
        book_counts[title] = book_counts.get(title, 0) + 1

    print(f"📊 Total Chunks in Database: {len(metadatas)}\n")
    print("📚 Books Breakdown:")
    for title, count in book_counts.items():
        print(f"   - {title}: {count} chunks")

    print("\n==================================================")


if __name__ == "__main__":
    xray_database()