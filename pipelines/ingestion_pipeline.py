import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from core.parsers.al_islam_parser import AlIslamEpubParser
from langchain_community.document_loaders import PyPDFLoader


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

        elif file_path.lower().endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            pdf_docs = loader.load()

            # برای PDF، اسم کتاب رو از اسم فایل درمیاریم (بدون پسوند .pdf)
            book_title = os.path.splitext(filename)[0]

            # تبدیل به فرمت استاندارد LangChain
            for doc in pdf_docs:
                # PyPDFLoader صفحات رو از 0 می‌شمره، پس +1 می‌کنیم
                page_num = doc.metadata.get("page", 0) + 1

                metadata = {
                    "book_title": book_title,
                    "chapter": f"صفحه {page_num}",
                    "footnotes": f"صفحه {page_num}"
                }
                langchain_docs.append(Document(page_content=doc.page_content, metadata=metadata))
        else:
            raise ValueError(f"❌ Unsupported file format for {filename}. Only .epub and .pdf are allowed.")

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