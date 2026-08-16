"""
Cross-lingual RAG pipeline: expand the question into three English queries,
search with MMR, then synthesise a cited answer in the user's own language.
"""

import logging

from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from core.config import get_settings

logger = logging.getLogger(__name__)

QUERY_GEN_TEMPLATE = """You are an expert in Shia history and theology.
The user will ask a question in their preferred language.
Your task is to extract the core intent and translate it into 3 different ENGLISH search queries to query a vector database.

1. Line 1: A modern, direct English translation of the query.
2. Line 2: A classical/traditional English query (using terms like 'concealment', 'tyrants', 'oppressors', 'progeny', 'occultation').
3. Line 3: A conceptual/academic English query.

Output ONLY the 3 English lines. No numbers, no bullet points, no extra text.

User's question: {question}
"""

QA_TEMPLATE = """You are a specialized researcher in Shia history, theology, and hadith.
Your task is to provide an accurate, analytical answer based on the provided Context.

Strict Rules:
1. Answer based ONLY on the provided Context.
2. Respond in the EXACT SAME LANGUAGE as the user's question (e.g., if the user asks in Persian, reply in Persian. If in English, reply in English. If in Arabic, reply in Arabic).
3. If the answer is found in the Context, provide a highly analytical response. At the end of your response, cite the sources strictly in this format (translate the labels like 'Chapter' and 'Book' to the user's language):
   - [Chapter Name] from [Book Name]
   - Primary References (Footnotes): [Insert FOOTNOTES content here]
4. The Golden Fallback Rule: If the Context is empty or does not contain the answer, you must output exactly this meaning (translated into the user's language):
   "My database (current books) lacks direct information on this matter. However, based on general knowledge of Shia history and theology:"
   Then, provide an academic and analytical answer from your internal knowledge. Do NOT include a "Sources/References" section in this case.
5. Do not hallucinate sources or facts.

Context (Extracted chunks from books):
{context}

User's question: {question}

Your analytical and documented response:
"""


class RetrievalPipeline:
    """
    Question-answering over a named Chroma collection.

    The collection name is explicit and mandatory. Both langchain_community and
    langchain_chroma default to a collection called "langchain" when it is
    omitted, which is how this pipeline previously ended up querying a bucket
    that no ingestion path deliberately writes to.
    """

    DEFAULT_COLLECTION = "theology"

    def __init__(self, container=None, collection: str | None = None):
        self.settings = container.settings if container else get_settings()
        self.collection = collection or self.DEFAULT_COLLECTION

        if container is not None:
            self.embeddings = container.embeddings
            store = container.store_for(self.collection)
            if store is None:
                raise ValueError(f"Unknown collection: {self.collection}")
            self.vectorstore = store
        else:
            # Standalone use (scripts, manual runs) still works.
            self.embeddings = OpenAIEmbeddings(
                model=self.settings.embedding_model,
                api_key=self.settings.openai_api_key,
            )
            self.vectorstore = Chroma(
                persist_directory=str(self.settings.chroma_dir),
                embedding_function=self.embeddings,
                collection_name=self.collection,
            )

        self.llm = ChatOpenAI(
            model=self.settings.theology_llm_model,
            temperature=0.2,
            api_key=self.settings.openai_api_key,
        )

        self.qa_prompt = PromptTemplate.from_template(QA_TEMPLATE)
        self.query_gen_prompt = PromptTemplate.from_template(QUERY_GEN_TEMPLATE)

    def _retriever(self, top_k: int):
        return self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": top_k,
                "fetch_k": self.settings.theology_fetch_k,
                "lambda_mult": self.settings.theology_lambda_mult,
            },
        )

    def ask(
        self,
        question: str,
        collection: str | None = None,
        top_k: int | None = None,
    ) -> dict:
        if collection and collection != self.collection:
            raise ValueError(
                f"This pipeline is bound to '{self.collection}', not '{collection}'"
            )

        top_k = top_k or self.settings.theology_top_k

        # 1. Expand the question into three English search perspectives.
        generated = (self.query_gen_prompt | self.llm).invoke(
            {"question": question}
        ).content
        queries = [q.strip() for q in generated.split("\n") if q.strip()]
        logger.info("expanded question into %d queries", len(queries))
        logger.debug("generated queries: %s", queries)

        # 2. Search each perspective, de-duplicating by content.
        retriever = self._retriever(top_k)
        unique_docs = []
        seen_contents: set[str] = set()
        for query in queries:
            for doc in retriever.invoke(query):
                if doc.page_content not in seen_contents:
                    seen_contents.add(doc.page_content)
                    unique_docs.append(doc)

        logger.info(
            "retrieved %d unique chunks from '%s'", len(unique_docs), self.collection
        )

        formatted_context = ""
        source_list: list[dict] = []
        for i, doc in enumerate(unique_docs):
            book = doc.metadata.get("book_title", "Unknown")
            chapter = doc.metadata.get("chapter", "Unknown")
            footnotes = doc.metadata.get("footnotes", "None")

            source_list.append(
                {"book_title": book, "chapter": chapter, "footnotes": footnotes}
            )
            formatted_context += (
                f"\n--- [Result {i + 1} | Book: {book} | Chapter: {chapter}] ---\n"
                f"TEXT: {doc.page_content}\n"
                f"FOOTNOTES (From Metadata): {footnotes}\n"
            )

        # Retrieved chunks are book text plus user questions -- never log them
        # at INFO. This used to print every chunk in full on every request.
        if self.settings.log_retrieved_chunks:
            logger.debug("context:\n%s", formatted_context)

        # 3. Synthesise the final answer.
        answer = self.llm.invoke(
            self.qa_prompt.format(context=formatted_context, question=question)
        )
        return {"answer": answer.content, "sources": source_list}
