import os
from typing import List
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from core.parsers.al_islam_parser import AlIslamEpubParser
from core.models import ParsedChunk

# لود کردن کلیدهای API از فایل .env
load_dotenv()

class IngestionPipeline:
    def __init__(self, db_directory: str = "./data/chroma_db"):
        self.db_directory = db_directory
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    def run(self, epub_path: str):
        print(f"\n🚀 Starting Ingestion Pipeline for: {epub_path}")

        # ۱. پارس کردن فایل EPUB
        print("1️⃣ Parsing EPUB and extracting metadata...")
        parser = AlIslamEpubParser(epub_path)
        parsed_chunks = parser.parse()

        book_title = parser.book_title
        print(f"   📖 Target Book: {book_title}")
        print(f"   ✅ Extracted {len(parsed_chunks)} enriched chunks.")

        # ۲. تبدیل به فرمت LangChain
        print("2️⃣ Converting to LangChain Documents...")
        langchain_docs = []
        for chunk in parsed_chunks:
            # مدیریت کلید پاورقی‌ها
            refs = chunk.metadata.get("footnotes", ["None"])
            refs_string = " | ".join(refs) if isinstance(refs, list) else refs

            metadata = {
                "book_title": chunk.metadata["book_title"],
                "chapter": chunk.metadata["chapter"],
                "footnotes": refs_string
            }
            doc = Document(page_content=chunk.text, metadata=metadata)
            langchain_docs.append(doc)

        # ۳. اتصال به دیتابیس موجود
        print("3️⃣ Connecting to existing ChromaDB...")
        vectorstore = Chroma(
            persist_directory=self.db_directory,
            embedding_function=self.embeddings
        )

        # ۴. عملیات جراحی: پاک کردن نسخه قدیمیِ فقط همین کتاب
        print(f"🧹 Checking for old versions of '{book_title}' in DB...")
        try:
            # دستور حذف بر اساس متادیتا (فقط رکوردهایی که اسم کتابشون مچ میشه)
            vectorstore._collection.delete(where={"book_title": book_title})
            print(f"   ✅ Old data for '{book_title}' successfully wiped. (Other books are SAFE!)")
        except Exception as e:
            # اگر دیتابیس خالی باشه یا کتاب برای بار اول اضافه بشه
            print("   ℹ️ No existing entries found. Proceeding as a new book.")

        # ۵. تزریق داده‌های جدید
        print(f"4️⃣ Generating Embeddings and injecting {len(langchain_docs)} chunks...")
        vectorstore.add_documents(documents=langchain_docs)

        print(f"🎉 Success! '{book_title}' is securely added to the AI brain.")
        return vectorstore