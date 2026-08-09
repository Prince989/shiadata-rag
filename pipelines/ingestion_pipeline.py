import os
import re  # 🚀 برای پارس کردن دقیق تگ‌های صفحه‌بندی
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from core.parsers.al_islam_parser import AlIslamEpubParser
from dotenv import load_dotenv

load_dotenv()

class IngestionPipeline:
    def __init__(self, db_directory: str = "./data/chroma_db", collection_name: str = "theology"):
        self.db_directory = db_directory
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    def run(self, file_path: str, force: bool = False):
        filename = os.path.basename(file_path)
        print(f"\n🚀 Processing: {filename}")

        langchain_docs = []
        book_title = ""

        # ۱. تشخیص هوشمند نوع فایل و پارس کردن
        if file_path.lower().endswith('.epub'):
            parser = AlIslamEpubParser(file_path)
            parsed_chunks = parser.parse()
            book_title = parser.book_title

            # تبدیل به فرمت استاندارد LangChain
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

        elif file_path.lower().endswith('.txt'):
            # برای فایل‌های متنی، اسم کتاب رو از اسم فایل درمیاریم
            book_title = os.path.splitext(filename)[0]

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 🚀 جادوی رگکس: جدا کردن متن بر اساس تگ‌های [جلد X - صفحه Y] که اسکرپر ساخته
            parts = re.split(r'---\s*\[(.*?)\]\s*---', content)

            # parts[0] معمولا قبل از اولین تگ هست (خالیه).
            # parts[1] تگ صفحه است، parts[2] متن صفحه، و به همین ترتیب...
            for i in range(1, len(parts), 2):
                page_meta = parts[i].strip()  # مثلا: جلد 2 - صفحه 60
                page_text = parts[i+1].strip()

                if page_text:  # اگر صفحه خالی نبود
                    metadata = {
                        "book_title": book_title,
                        "chapter": page_meta,
                        "footnotes": page_meta
                    }
                    langchain_docs.append(Document(page_content=page_text, metadata=metadata))
        else:
            raise ValueError(f"❌ Unsupported file format for {filename}. Only .epub and .txt are allowed.")

        print(f"   📖 Target Book: {book_title}")

        # ۲. اتصال به دیتابیس
        vectorstore = Chroma(
            persist_directory=self.db_directory,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
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

        print(f"   ✅ Extracted {len(langchain_docs)} enriched chunks. Starting embedding...")

        # ۴. تزریق داده‌های جدید به دیتابیس (تماس با OpenAI)
        vectorstore.add_documents(documents=langchain_docs)

        print(f"🎉 Success! '{book_title}' is securely added to the AI brain.")
        return vectorstore