# 🧠 SHIA-DATA AI ENGINE (Advanced RAG)

An advanced, multi-lingual Retrieval-Augmented Generation (RAG) engine designed to understand, analyze, and answer complex theological, historical, and jurisprudential questions based on Shia Islamic texts.

Built for enterprise-level scalability, this system ingests raw EPUB books, vectorizes them with deep contextual awareness, and serves as an intelligent, hallucination-free research assistant.

## ✨ Core Architecture & Features

### ⚙️ Section-Based Contextual Chunking: 
Instead of blindly splitting texts by character count, the parser intelligently groups paragraphs under their respective headers (\<h2>, \<h3>), preserving the narrative flow, arguments, and associated footnotes as single, cohesive vectors.

### 🌐 Cross-Lingual Query Translator: 
Users can interact with the system in any language (e.g., Persian, Arabic, Urdu). The engine uses a One-Shot Prompt to translate and expand the user's query into three distinct English search perspectives (Modern, Classical, and Academic) before querying the database, ensuring maximum retrieval accuracy across classical texts.

### ⚖️ MMR (Maximal Marginal Relevance) Search:
Prevents "Multi-Document Starvation". By optimizing for both similarity and diversity, the retrieval pipeline ensures that a single book does not monopolize the search results, drawing answers from a wide array of sources.

### 🛡️ Anti-Hallucination Fallback: 
The engine is bound by strict prompt constraints. If the vector database lacks direct evidence, it refuses to hallucinate facts. Instead, it explicitly informs the user about the missing data before safely falling back on its general theological knowledge.

### ♻️ Idempotent Batch Ingestion: 
A smart CLI designed for seamless database lifecycle management. It automatically detects and skips previously ingested books to save API costs, while allowing targeted overwrites (--force) or complete database rebuilds (--force-all).

## 🛠️ Prerequisites

To run this project, you will need:

Python 3.9+

A valid OpenAI API Key (with available credits for Embeddings and GPT-4o-mini).

### 📦 Installation & Setup

Clone the repository:

``` bash 
git clone <repository_url>
cd AIEngine
```

Install the required dependencies:
``` bash
pip install -r requirements.txt
pip install -U langchain-chroma
```

Configure Environment Variables:
Create a .env file in the root directory and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

## 📥 Download Pre-built Vector Database (Recommended)

To save time and OpenAI API costs (for embeddings), you do not need to ingest all books from scratch. We have provided a fully ingested, structured Vector Database containing major Shia texts (Rijal, Fiqh, History, Theology, etc.).

**How to add the database to your project:**

1. Go to the [ShiaData Database Releases Page](https://github.com/Prince989/shiadata-rag/releases).
2. Download the compressed database file (e.g., `.zip` or `.tar.gz`) from the **Assets** section.
3. Extract the downloaded file.
4. Place the extracted `chroma_db` folder directly into the `data/` directory of your project.

Your structure should look exactly like this:
```text
SHIA-DATA-AI/
├── data/
│   ├── raw_epubs/
│   └── chroma_db/      <-- Place the extracted database folder here!
```

### 📚 Database Management (Data Ingestion)

Place your raw Islamic texts (.epub format) inside the data/raw_epubs/ directory. Use the robust ingestion CLI to manage your vector database:

Standard Ingestion (Smart Skip for existing books):

python ingest.py


Targeted Overwrite (Force re-ingest a specific book):

``` python
python ingest.py --force "al-ghayba.epub"
```

### Nuclear Option (Wipe the database and rebuild from scratch):

``` python
python ingest.py --force-all
```

### 💬 Usage (Terminal Chatbot)

To interact with the AI Engine directly via the terminal, run:

``` python
python main.py
```

Pro Tip: You can ask your questions in any language. The engine will automatically translate the intent, search the English database, and reply in your original language, complete with highly accurate footnote citations.

### 📂 Directory Structure

``` 
SHIA-DATA-AI/
├── core/
│   └── parsers/
│       └── al_islam_parser.py      # Intelligent EPUB parser & Footnote extractor
├── data/
│   ├── raw_epubs/                  # Drop your .epub books here
│   └── chroma_db/                  # Auto-generated Vector Database
├── pipelines/
│   ├── ingestion_pipeline.py       # Handles Chunking, Vectorization, and Upserts
│   └── retrieval_pipeline.py       # Handles Query Translation, MMR, and Synthesis
├── .env                            # Environment variables (Ignored in Git)
├── ingest.py                       # CLI tool for smart data ingestion
└── main.py                         # Interactive terminal entry point
```

Architected with ❤️ for the development of Islamic AI Systems.
