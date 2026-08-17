"""
Service container built once at startup and shared by every request.

Before this existed, each route module constructed its own services at import
time. That produced 10 Chroma handles and 10 embedding clients at boot (3x
RijalService, 2x QuranService, 2x HadithService), and -- worse -- a missing
Google API key raised inside LLMGateway *during import*, which killed the whole
application before uvicorn could serve anything at all.

Now each subsystem is built defensively. A failure is recorded in `degraded`
and only the routes that depend on that subsystem return 503. In particular the
pure-vector search endpoint stays fully alive with no LLM credentials at all,
which is exactly the failure mode a retrieval microservice should have.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from core.config import Settings
from core.paths import KNOWN_COLLECTIONS, LANGCHAIN_DEFAULT_COLLECTION

logger = logging.getLogger(__name__)


@dataclass
class ServiceContainer:
    settings: Settings
    embeddings: OpenAIEmbeddings
    stores: dict[str, Chroma] = field(default_factory=dict)

    # Built lazily/defensively; None means "unavailable, see degraded".
    rijal_index: Any = None
    theology: Any = None
    rijal: Any = None
    hadith: Any = None
    ijtihad: Any = None
    conflict: Any = None

    degraded: dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    def collection_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for name, store in self.stores.items():
            try:
                counts[name] = store._collection.count()
            except Exception as exc:  # pragma: no cover - diagnostics only
                logger.warning("could not count collection %s: %s", name, exc)
                counts[name] = -1
        return counts

    def store_for(self, collection: str) -> Chroma | None:
        return self.stores.get(collection)


def build_container(settings: Settings) -> ServiceContainer:
    """Construct every shared dependency. Never raises for LLM-only failures."""
    chroma_path = settings.chroma_dir
    sqlite_path = chroma_path / "chroma.sqlite3"
    if not sqlite_path.exists():
        # Chroma would happily create an empty DB here and every search would
        # return nothing with no error. Refuse to start instead.
        raise RuntimeError(
            f"No Chroma database at {sqlite_path}. "
            "Refusing to start rather than silently creating an empty one."
        )

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )
    container = ServiceContainer(settings=settings, embeddings=embeddings)

    for name in KNOWN_COLLECTIONS:
        container.stores[name] = Chroma(
            persist_directory=str(chroma_path),
            embedding_function=embeddings,
            collection_name=name,
        )

    _warn_on_default_collection(container)
    container.rijal_index = _build_rijal_index(container)
    _build_services(container)
    return container


def _build_rijal_index(container: ServiceContainer):
    from services.rijal_index import RijalIndex

    store = container.store_for("rijal")
    if store is None:
        return None
    try:
        index = RijalIndex.build(store)
        logger.info("rijal index built: %d entries", len(index))
        return index
    except Exception as exc:
        container.degraded["rijal_index"] = f"{type(exc).__name__}: {exc}"
        logger.error("failed to build rijal index: %s", exc)
        return None


def _warn_on_default_collection(container: ServiceContainer) -> None:
    """
    Detect the landmine: a collection literally named "langchain".

    Both langchain_community.Chroma and langchain_chroma.Chroma default to this
    name when collection_name is omitted, so its existence means some code path
    is writing into an unnamed bucket that no service reads from.
    """
    try:
        probe = Chroma(
            persist_directory=str(container.settings.chroma_dir),
            embedding_function=container.embeddings,
            collection_name=LANGCHAIN_DEFAULT_COLLECTION,
        )
        count = probe._collection.count()
    except Exception:
        return

    if count > 0:
        logger.critical(
            "Collection %r exists with %d vectors. Some Chroma(...) call is "
            "missing collection_name and is writing to the default bucket. "
            "Nothing reads from it.",
            LANGCHAIN_DEFAULT_COLLECTION,
            count,
        )


def _build_services(container: ServiceContainer) -> None:
    """Build each subsystem in isolation so one failure cannot cascade."""
    # Imported here rather than at module scope: these modules pull in LLM SDKs,
    # and a failure importing one must not prevent the others from building.
    def _theology():
        from services.theology_service import TheologyService

        return TheologyService(container=container)

    def _rijal():
        from services.rijal_service import RijalService

        return RijalService(container=container)

    def _hadith():
        from services.hadith_service import HadithService

        return HadithService(container=container)

    def _ijtihad():
        from services.ijtihad_service import IjtihadService

        return IjtihadService(container=container)

    def _conflict():
        from services.conflict_resolver_service import ConflictResolverService

        return ConflictResolverService(container=container)

    for attr, builder in (
        ("theology", _theology),
        ("rijal", _rijal),
        ("hadith", _hadith),
        ("ijtihad", _ijtihad),
        ("conflict", _conflict),
    ):
        try:
            setattr(container, attr, builder())
            logger.info("subsystem %s ready", attr)
        except Exception as exc:
            container.degraded[attr] = f"{type(exc).__name__}: {exc}"
            logger.error("subsystem %s DEGRADED: %s", attr, exc)
