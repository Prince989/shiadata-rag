"""Shared helpers for turning Chroma hits into API responses."""

from typing import Any

from langchain_core.documents import Document

from schemas.responses import RetrievedDocument


def build_where(filters: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Translate a flat filter dict into a Chroma `where` clause.

    Chroma rejects a bare multi-key dict such as {"a": 1, "b": 2}; several keys
    must be wrapped in $and. The existing services never hit this because they
    only ever passed a single key, so the bug was latent until the generic
    search endpoint made multi-key filters reachable.
    """
    if not filters:
        return None
    if len(filters) == 1:
        return dict(filters)
    return {"$and": [{key: value} for key, value in filters.items()]}


def to_retrieved_document(
    doc: Document, distance: float | None = None
) -> RetrievedDocument:
    metadata = dict(doc.metadata or {})
    return RetrievedDocument(
        content=doc.page_content,
        metadata=metadata,
        distance=distance,
        book_title=metadata.get("book_title"),
        chapter=metadata.get("chapter"),
        domain=metadata.get("domain"),
    )
