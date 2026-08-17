"""
Generic vector search across any collection.

This is the endpoint the NestJS backend is built around: it is the only route
that returns full metadata for arbitrary collections with arbitrary filters,
and it makes zero LLM calls, so it stays available even when every LLM
subsystem is degraded.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import ContainerDep, get_container
from core.container import ServiceContainer
from schemas.requests import VectorSearchRequest
from schemas.responses import CollectionInfo, SearchResponse
from services.search_utils import build_where, to_retrieved_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/search", tags=["Vector Search"])


@router.post("", response_model=SearchResponse, summary="جستجوی برداری عمومی")
def vector_search(
    request: VectorSearchRequest,
    container: ContainerDep,
) -> SearchResponse:
    store = container.store_for(request.collection)
    if store is None:
        raise HTTPException(
            status_code=404, detail=f"Unknown collection '{request.collection}'"
        )

    where = build_where(request.filters)

    try:
        if request.search_type == "mmr":
            # MMR does not expose distances.
            hits = [
                (doc, None)
                for doc in store.max_marginal_relevance_search(
                    request.query,
                    k=request.top_k,
                    fetch_k=request.fetch_k,
                    lambda_mult=request.lambda_mult,
                    filter=where,
                )
            ]
        elif request.include_distances:
            # similarity_search_with_score returns the RAW distance. We
            # deliberately avoid similarity_search_with_relevance_scores:
            # every collection here has hnsw:space unset, so the metric is L2,
            # and langchain's euclidean relevance function emits negative
            # "scores" for distances above sqrt(2). Raw distance is
            # well-defined; the caller ranks.
            hits = store.similarity_search_with_score(
                request.query, k=request.top_k, filter=where
            )
        else:
            hits = [
                (doc, None)
                for doc in store.similarity_search(
                    request.query, k=request.top_k, filter=where
                )
            ]
    except Exception as exc:
        logger.error("search failed on %s: %s", request.collection, exc)
        raise HTTPException(status_code=500, detail=f"Vector search failed: {exc}")

    return SearchResponse(
        collection=request.collection,
        query=request.query,
        total_found=len(hits),
        documents=[to_retrieved_document(doc, dist) for doc, dist in hits],
    )


@router.get(
    "/collections",
    response_model=list[CollectionInfo],
    summary="فهرست کالکشن‌ها و کلیدهای متادیتا",
)
def list_collections(
    container: ServiceContainer = Depends(get_container),
) -> list[CollectionInfo]:
    """
    Discovery endpoint. The four collections carry substantially different
    metadata keys, so callers need this to know what is filterable where.
    """
    infos: list[CollectionInfo] = []
    for name, store in container.stores.items():
        try:
            count = store._collection.count()
            keys: set[str] = set()
            if count:
                sample = store._collection.get(limit=50, include=["metadatas"])
                for meta in sample.get("metadatas") or []:
                    keys.update((meta or {}).keys())
            infos.append(
                CollectionInfo(name=name, count=count, metadata_keys=sorted(keys))
            )
        except Exception as exc:
            logger.warning("could not inspect collection %s: %s", name, exc)
            infos.append(CollectionInfo(name=name, count=-1, metadata_keys=[]))
    return infos
