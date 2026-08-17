from langchain_core.documents import Document

from services.rijal_index import RijalIndex


class _FakeStore:
    def __init__(self, docs: list[Document]):
        self._docs = docs

    def get(self, include=None):
        return {
            "documents": [d.page_content for d in self._docs],
            "metadatas": [d.metadata for d in self._docs],
        }


def _index_from(*texts_and_meta):
    docs = [Document(page_content=t, metadata=m) for t, m in texts_and_meta]
    return RijalIndex.build(_FakeStore(docs))


def test_build_from_store():
    index = _index_from(
        ("ابراهيم بن هاشم = ثقة", {"book_title": "A"}),
        ("زراره بن اعین = مجهول", {"book_title": "B"}),
    )
    assert len(index) == 2


def test_vocalized_needle_finds_unvocalized_document():
    index = _index_from(("محمد بن يحيى ثقة است", {"book_title": "A"}))
    hits = index.lookup("مُحَمَّدُ بْنُ يَحْيَى")
    assert len(hits) == 1
    assert hits[0].metadata["book_title"] == "A"


def test_no_match_returns_empty():
    index = _index_from(("زراره بن اعین", {"book_title": "A"}))
    assert index.lookup("someone else entirely") == []


def test_line_initial_match_scores_first():
    index = _index_from(
        (
            "این متن به ابراهيم اشاره‌ای گذرا دارد.",
            {"book_title": "mention-only"},
        ),
        (
            "ابراهيم بن هاشم = ثقة\nنظر علما درباره او مثبت است.",
            {"book_title": "authoritative"},
        ),
    )
    hits = index.lookup("ابراهيم")
    assert hits[0].metadata["book_title"] == "authoritative"


def test_limit_is_respected():
    index = _index_from(
        *[(f"زراره در سند شماره {i}", {"book_title": f"book-{i}"}) for i in range(10)]
    )
    hits = index.lookup("زراره", limit=3)
    assert len(hits) == 3
