"""
In-memory, normalized narrator index over the rijal collection.

Replaces three copy-pasted blocks (rijal_service.py, ijtihad_service.py,
conflict_resolver_service.py) that each called
`vectorstore.get(include=["documents", "metadatas"])` -- dumping all 12,941
rijal documents into RAM on EVERY request, twice per conflict-resolution call.
Measured cost of that call alone: ~0.4-0.8s and ~70MB of heap churn.

Built once at startup instead. Both the needle (narrator name) and the
haystack (document text) are normalized through the same function, which also
fixes two latent bugs in the old code:
  - the old "ar" variant replaced every alef with alef-hamza, corrupting names
  - vocalized narrator names (as returned by HadithService.extract_sanad)
    matched zero documents, since ~86% of the corpus carries no diacritics

An SQLite FTS or inverted index was considered and rejected: those match
tokens/prefixes, not arbitrary substrings of multi-word Arabic names, and
would silently change which narrator entries surface in already-validated
scholarly output. A linear scan over ~13k short strings costs low
single-digit milliseconds, which is negligible next to the 2-5s LLM call each
lookup feeds into.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_core.documents import Document

from core.text_normalize import normalize_ar

# Keywords that signal a verdict is stated in this chunk. Written in
# normalized form because they are tested against the normalized haystack.
_VERDICT_MARKERS = ("=", "ضعیف", "ثقه", "ثقة", "صحیح", "مجهول")


@dataclass(frozen=True)
class _Entry:
    normalized: str
    raw: str
    metadata: dict


class RijalIndex:
    """Built once via RijalIndex.build(store), then shared across services."""

    __slots__ = ("_entries",)

    def __init__(self, entries: list[_Entry]):
        self._entries = entries

    def __len__(self) -> int:
        return len(self._entries)

    @classmethod
    def build(cls, store) -> "RijalIndex":
        data = store.get(include=["documents", "metadatas"])
        docs = data.get("documents") or []
        metas = data.get("metadatas") or []
        entries = [
            _Entry(normalized=normalize_ar(text), raw=text, metadata=meta or {})
            for text, meta in zip(docs, metas)
        ]
        return cls(entries)

    def lookup(self, narrator: str, limit: int = 5) -> list[Document]:
        """
        Exact (normalized) substring match, ranked the same way the original
        code ranked it: a line-initial match scores highest, a chunk that also
        contains a verdict keyword scores higher, shorter chunks edge out
        longer ones as a tiebreak.
        """
        needle = normalize_ar(narrator)
        if not needle:
            return []

        escaped = re.escape(needle)
        line_initial = re.compile(r"(^|\n|-)\s*" + escaped)

        hits: list[tuple[float, _Entry]] = []
        for entry in self._entries:
            if needle not in entry.normalized:
                continue
            score = 100.0 if line_initial.search(entry.normalized) else 0.0
            if any(marker in entry.normalized for marker in _VERDICT_MARKERS):
                score += 50.0
            score -= len(entry.normalized) / 1000.0
            hits.append((score, entry))

        hits.sort(key=lambda pair: pair[0], reverse=True)
        return [
            Document(page_content=entry.raw, metadata=entry.metadata)
            for _, entry in hits[:limit]
        ]
