import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()


class RetrievalPipeline:
    """
    پایپ‌لاین پرسش و پاسخ (RAG).
    سوال را می‌گیرد، در دیتابیس جستجو می‌کند و با کمک LLM پاسخ نهایی و منابع را تولید می‌کند.
    """

    def __init__(self, db_directory: str = "./data/chroma_db"):
        self.db_directory = db_directory
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

        self.vectorstore = Chroma(
            persist_directory=self.db_directory,
            embedding_function=self.embeddings
        )
        # تنظیمِ جستجو: ۵ نتیجه‌ی برتر را بیاور (Top-K = 5)
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 7,  # تعداد نتایج نهایی که به LLM می‌دیم
                "fetch_k": 30,  # تعداد متونی که اول از کل دیتابیس‌ها می‌کشه بیرون
                "lambda_mult": 0.5,  # ضریب تنوع (بین 0 تا 1). 0.5 یعنی 50% شباهت به سوال + 50% تنوعِ منابع
                # "filter": {"book_title": "Kitab Al Ghayba_ The Book Of Occultation"}
            }
        )

        # 2. طراحی System Prompt (دستورات سخت‌گیرانه برای جلوگیری از توهم)
        query_gen_template = """You are an expert in Shia history and theology.
The user will ask a question in their preferred language.
Your task is to extract the core intent and translate it into 3 different ENGLISH search queries to query a vector database.

1. Line 1: A modern, direct English translation of the query.
2. Line 2: A classical/traditional English query (using terms like 'concealment', 'tyrants', 'oppressors', 'progeny', 'occultation').
3. Line 3: A conceptual/academic English query.

Output ONLY the 3 English lines. No numbers, no bullet points, no extra text.

User's question: {question}
"""
        qa_template = """You are a specialized researcher in Shia history, theology, and hadith.
        Your task is to provide an accurate, analytical answer based on the provided Context.

        Strict Rules:
        1. Answer based ONLY on the provided Context.
        2. Respond in the EXACT SAME LANGUAGE as the user's question (e.g., if the user asks in Persian, reply in Persian. If in English, reply in English. If in Arabic, reply in Arabic).
        3. If the answer is found in the Context, provide a highly analytical response. At the end of your response, cite the sources strictly in this format (translate the labels like 'Chapter' and 'Book' to the user's language):
           - [Chapter Name] from [Book Name]
           - Primary References (Footnotes): [Insert FOOTNOTES content here]
        4. ⚠️ The Golden Fallback Rule: If the Context is empty or does not contain the answer, you must output exactly this meaning (translated into the user's language):
           "My database (current books) lacks direct information on this matter. However, based on general knowledge of Shia history and theology:"
           Then, provide an academic and analytical answer from your internal knowledge. Do NOT include a "Sources/References" section in this case.
        5. Do not hallucinate sources or facts.

        Context (Extracted chunks from books):
        {context}

        User's question: {question}

        Your analytical and documented response:
        """
        self.qa_prompt = PromptTemplate.from_template(qa_template)

        self.query_gen_prompt = PromptTemplate.from_template(query_gen_template)

    def ask(self, question: str):
        # مرحله اول: تولید ۳ کوئری انگلیسی هوشمند
        print(f"\n🌐 1. Translating and Expanding Query...")
        query_chain = self.query_gen_prompt | self.llm
        generated_queries_text = query_chain.invoke({"question": question}).content

        # جدا کردن خطوط برای ساخت لیست کوئری‌ها
        queries = [q.strip() for q in generated_queries_text.split('\n') if q.strip()]

        print("\n" + "-" * 40)
        print("🎯 SMART QUERIES GENERATED:")
        for i, q in enumerate(queries):
            print(f"   {i + 1}. {q}")
        print("-" * 40)

        # مرحله دوم: جستجوی هر ۳ کوئری در دیتابیس و حذف متون تکراری
        print("\n🔍 2. Searching database with multiple perspectives...")
        unique_docs = []
        seen_contents = set()

        for q in queries:
            docs = self.retriever.invoke(q)
            for doc in docs:
                if doc.page_content not in seen_contents:
                    unique_docs.append(doc)
                    seen_contents.add(doc.page_content)

        print("\n" + "=" * 40)
        print(f"📥 CONTEXT EXTRACTED (Total Unique Chunks: {len(unique_docs)}):")
        print("=" * 40)

        formatted_context = ""
        for i, doc in enumerate(unique_docs):
            book = doc.metadata.get('book_title', 'Unknown')
            chapter = doc.metadata.get('chapter', 'Unknown')
            footnotes = doc.metadata.get('footnotes', 'None')

            chunk_text = (
                f"\n--- [Result {i + 1} | Book: {book} | Chapter: {chapter}] ---\n"
                f"TEXT: {doc.page_content}\n"
                f"FOOTNOTES (From Metadata): {footnotes}\n"
            )
            formatted_context += chunk_text
            print(chunk_text)

        print("=" * 40 + "\n")

        # مرحله سوم: ارسال به LLM برای پاسخگویی نهایی
        print("🤖 3. Synthesizing final answer...")
        final_prompt = self.qa_prompt.format(
            context=formatted_context,
            question=question
        )

        answer = self.llm.invoke(final_prompt)
        return answer.content