"""
Shared fixtures. Everything here is network-free: no real Chroma, no real LLM.

The three files that used to live in tests/ built live services (Chroma,
Gemini, OpenAI clients) at import time and had zero assertions -- merely
collecting them fired real API calls. They've been moved unchanged to
scripts/manual/ as manual smoke scripts; pytest is configured (pyproject.toml
testpaths) to never look there.
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Settings requires OPENAI_API_KEY to construct. Provide a harmless dummy
# before anything imports core.config, so tests never depend on a real .env.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-not-real")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")


class FakeChromaCollection:
    def __init__(self, count: int = 3):
        self._count = count

    def count(self) -> int:
        return self._count

    def get(self, limit=None, include=None):
        metas = [{"book_title": "Fake Book", "domain": "history"}] * self._count
        return {"metadatas": metas[: limit or self._count]}


class FakeStore:
    """Stands in for a langchain_chroma.Chroma instance."""

    def __init__(self, docs: list[Document] | None = None):
        self._docs = docs or [
            Document(
                page_content="sample content",
                metadata={"book_title": "Fake Book", "chapter": "Ch 1", "domain": "history"},
            )
        ]
        self._collection = FakeChromaCollection(count=len(self._docs))
        self.last_filter = None
        self.last_search_type = None

    def similarity_search(self, query, k=5, filter=None):
        self.last_filter = filter
        self.last_search_type = "similarity"
        return self._docs[:k]

    def similarity_search_with_score(self, query, k=5, filter=None):
        self.last_filter = filter
        self.last_search_type = "similarity_with_score"
        return [(doc, 1.0 + i * 0.1) for i, doc in enumerate(self._docs[:k])]

    def max_marginal_relevance_search(self, query, k=5, fetch_k=30, lambda_mult=0.5, filter=None):
        self.last_filter = filter
        self.last_search_type = "mmr"
        return self._docs[:k]


class FakeContainer:
    """Minimal stand-in for core.container.ServiceContainer."""

    def __init__(self):
        self.settings = _FakeSettings()
        self.stores = {
            "theology": FakeStore(),
            "hadith": FakeStore(),
            "rijal": FakeStore(),
            "quran": FakeStore(),
        }
        self.rijal_index = None
        self.theology = None
        self.rijal = None
        self.hadith = None
        self.ijtihad = None
        self.conflict = None
        self.degraded: dict[str, str] = {}

    def store_for(self, name):
        return self.stores.get(name)

    def collection_counts(self):
        return {name: store._collection.count() for name, store in self.stores.items()}


class _FakeSettings:
    internal_api_key = "test-internal-key"


@pytest.fixture
def fake_container() -> FakeContainer:
    return FakeContainer()


@pytest.fixture
def client(fake_container):
    """
    TestClient with app.state.container overridden -- no real Chroma DB, no
    LLM calls.

    Deliberately NOT used as a context manager: Starlette only fires the
    app's lifespan (which builds the REAL container against the real Chroma
    DB and real LLM clients) when TestClient is entered via `with`. Setting
    app.state.container directly and skipping `with` gets every route the
    fake container without ever touching the network.
    """
    from main import app

    app.state.container = fake_container
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"X-Internal-API-Key": "test-internal-key"}
