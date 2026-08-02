import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from core.parsers.al_islam_parser import AlIslamEpubParser


class IngestionPipeline:
    def __init__(self, db_directory: str = "./data/chroma_db"):
        self.db_directory = db_directory
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    def run(self, epub_path: str, force: bool = False):
        filename = os.path.basename(epub_path)
        print(f"\n🚀 Processing: {filename}")

        # ۱. پارس کردن فایل EPUB (این مرحله رایگان و آفلاین است)
        parser = AlIslamEpubParser(epub_path)
        parsed_chunks = parser.parse()
        book_title = parser.book_title
        print(f"   📖 Target Book: {book_title}")

        # ۲. اتصال به دیتابیس
        vectorstore = Chroma(
            persist_directory=self.db_directory,
            embedding_function=self.embeddings
        )

        # ۳. هوشِ تشخیص تکرار (بررسی دیتابیس)
        existing_docs = vectorstore.get(where={"book_title": book_title})
        book_exists = existing_docs and len(existing_docs.get('ids', [])) > 0

        # اگر کتاب هست و کاربر دستور Force نداده -> Skip
        if book_exists and not force:
            print(f"   ⏭️  SKIPPED: '{book_title}' is already in the database.")
            print(f"   💡 (Use --force \"{filename}\" to overwrite)")
            return vectorstore

        # اگر کتاب هست ولی کاربر دستور Force داده -> Delete old data
        if book_exists and force:
            print(f"   🧹 OVERRIDE: Wiping old data for '{book_title}'...")
            try:
                vectorstore._collection.delete(where={"book_title": book_title})
                print("   ✅ Old data wiped successfully.")
            except Exception as e:
                print(f"   ⚠️ Could not delete old data: {e}")

        print(f"   ✅ Extracted {len(parsed_chunks)} enriched chunks. Starting embedding...")

        # ۴. تبدیل به فرمت LangChain
        langchain_docs = []
        for chunk in parsed_chunks:
            refs = chunk.metadata.get("footnotes", ["None"])
            refs_string = " | ".join(refs) if isinstance(refs, list) else refs

            metadata = {
                "book_title": chunk.metadata["book_title"],
                "chapter": chunk.metadata["chapter"],
                "footnotes": refs_string
            }
            doc = Document(page_content=chunk.text, metadata=metadata)
            langchain_docs.append(doc)

        # ۵. تزریق داده‌های جدید به دیتابیس (تماس با OpenAI)
        vectorstore.add_documents(documents=langchain_docs)

        print(f"🎉 Success! '{book_title}' is securely added to the AI brain.")
        return vectorstore