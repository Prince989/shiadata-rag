import os
import re
import json
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from core.parsers.al_islam_parser import AlIslamEpubParser
from dotenv import load_dotenv

load_dotenv()


class IngestionPipeline:
    def __init__(self, db_directory: str | None = None, collection_name: str = "theology"):
        from core.config import get_settings
        from core.paths import CATALOG_PATH

        settings = get_settings()
        # Absolute by default. A relative Chroma path does not error when the
        # working directory is wrong -- it silently creates a new empty DB.
        self.db_directory = str(db_directory or settings.chroma_dir)
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model, api_key=settings.openai_api_key
        )

        self.catalog_path = str(CATALOG_PATH)
        self.catalog = self._load_catalog()

    def _load_catalog(self):
        """خواندن فایل کاتالوگ در صورت وجود"""
        if os.path.exists(self.catalog_path):
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                return json.load(f)

        print(f"\n⚠️ CRITICAL WARNING: Could not find catalog file at: {os.path.abspath(self.catalog_path)}")
        print("⚠️ Using empty metadata fallback!\n")

        return {"default_metadata": {"domain": "general"}, "books": {}}

    def _get_smart_metadata(self, filename: str):
        """تولید متادیتای داینامیک بر اساس فایل JSON و نام فایل"""
        base_name = filename.rsplit('.', 1)[0]
        ext = filename.rsplit('.', 1)[1].lower()

        # پیدا کردن نام کتاب و جلد (مثال: vasael-o-shia-23)
        match = re.match(r"(.+?)(?:-(\d+))?$", base_name)
        if not match:
            return self.catalog.get("default_metadata", {})

        book_key = match.group(1).lower()
        volume = match.group(2)

        # جستجو در کاتالوگ
        matched_book = next((k for k in self.catalog["books"] if k.lower() in book_key), None)

        if matched_book:
            book_info = self.catalog["books"][matched_book]
            if "volumes" in book_info and volume:
                meta = book_info["volumes"].get(volume, book_info["volumes"].get("default", {}))
            else:
                meta = {k: v for k, v in book_info.items() if k != "volumes"}

            meta["book_name"] = matched_book
            if volume:
                meta["volume"] = volume
            meta["file_type"] = ext

            # پر کردن مقادیر پیش‌فرض
            for k, v in self.catalog.get("default_metadata", {}).items():
                meta.setdefault(k, v)
            return meta

        return self.catalog.get("default_metadata", {})

    def run(self, file_path: str, force: bool = False):
        filename = os.path.basename(file_path)
        print(f"\n🚀 Processing: {filename}")

        # 🧠 دریافت متادیتای هوشمند برای این فایل
        smart_metadata = self._get_smart_metadata(filename)

        langchain_docs = []

        # 🚀 [رفع باگ]: اضافه کردن شماره جلد به نام کتاب برای جلوگیری از تداخل
        base_name = smart_metadata.get("book_name", os.path.splitext(filename)[0])
        vol_num = smart_metadata.get("volume")

        # اگر فایل شماره جلد داره، اسم کتاب رو یکتا می‌کنیم (مثلاً al-ehtejaj-1)
        book_title = f"{base_name}-{vol_num}" if vol_num else base_name
        smart_metadata["book_title"] = book_title

        # ۱. تشخیص هوشمند نوع فایل و پارس کردن
        if file_path.lower().endswith('.epub'):
            parser = AlIslamEpubParser(file_path)
            parsed_chunks = parser.parse()
            # book_title رو از پارسر خودت می‌گیریم تا دقیق‌تر باشه
            book_title = parser.book_title
            smart_metadata["book_title"] = book_title

            for chunk in parsed_chunks:
                refs = chunk.metadata.get("footnotes", ["None"])
                refs_string = " | ".join(refs) if isinstance(refs, list) else refs

                # 💡 ترکیب متادیتای هوشمند با متادیتای پارسر تو
                metadata = {
                    **smart_metadata,
                    "chapter": chunk.metadata["chapter"],
                    "footnotes": refs_string
                }
                doc = Document(page_content=chunk.text, metadata=metadata)
                langchain_docs.append(doc)

        elif file_path.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            parts = re.split(r'---\s*\[(.*?)\]\s*---', content)

            for i in range(1, len(parts), 2):
                page_meta = parts[i].strip()
                page_text = parts[i + 1].strip()

                if page_text:
                    # 💡 ترکیب متادیتای هوشمند با متادیتای Regex تو
                    metadata = {
                        **smart_metadata,
                        "book_title": book_title,
                        "chapter": page_meta,
                        "footnotes": page_meta
                    }
                    langchain_docs.append(Document(page_content=page_text, metadata=metadata))
        else:
            raise ValueError(f"❌ Unsupported file format for {filename}. Only .epub and .txt are allowed.")

        print(f"   📖 Target Book: {book_title}")
        print(f"   🏷️  Injected Domain: {smart_metadata.get('domain', 'Unknown')}")

        # ۲. اتصال به دیتابیس
        vectorstore = Chroma(
            persist_directory=self.db_directory,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
        )

        # ۳. هوشِ تشخیص تکرار
        existing_docs = vectorstore.get(where={"book_title": book_title})
        book_exists = existing_docs and len(existing_docs.get('ids', [])) > 0

        if book_exists and not force:
            print(f"   ⏭️  SKIPPED: '{book_title}' is already in the database.")
            print(f"   💡 (Use --force \"{filename}\" to overwrite)")
            return vectorstore

        if book_exists and force:
            print(f"   🧹 OVERRIDE: Wiping old data for '{book_title}'...")
            try:
                vectorstore._collection.delete(where={"book_title": book_title})
                print("   ✅ Old data wiped successfully.")
            except Exception as e:
                print(f"   ⚠️ Could not delete old data: {e}")

        print(f"   ✅ Extracted {len(langchain_docs)} enriched chunks. Starting embedding...")

        # ۴. تزریق داده‌های جدید به دیتابیس
        vectorstore.add_documents(documents=langchain_docs)

        print(f"🎉 Success! '{book_title}' is securely added to the AI brain.")
        return vectorstore