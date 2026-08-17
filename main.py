"""
SHIA-DATA AI Engine -- internal retrieval microservice.

This service is NOT internet-facing. It sits behind the NestJS backend, which
is its only client. Consequently it binds to localhost by default, guards every
data route with a shared secret, and carries no CORS middleware at all (CORS is
a browser mechanism and does not apply to a server-side HTTP client).
"""

import logging
from contextlib import asynccontextmanager

import anyio.to_thread
import uvicorn
from fastapi import Depends, FastAPI

from api.dependencies import get_container, require_api_key
from api.routes import chat, hadith, ijtihad, rijal, search, story, theology
from core.config import get_settings
from core.container import ServiceContainer, build_container
from schemas.responses import HealthResponse

logging.basicConfig(
    level=get_settings().log_level,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)
logger = logging.getLogger("shiadata")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Bound the threadpool. Plain `def` handlers run here, and each heavy
    # rijal request holds a large working set -- 40 simultaneous ones (anyio's
    # default) would be an out-of-memory event.
    anyio.to_thread.current_default_thread_limiter().total_tokens = (
        settings.thread_pool_size
    )

    logger.info("building service container from %s", settings.chroma_dir)
    container = await anyio.to_thread.run_sync(build_container, settings)
    app.state.container = container

    counts = container.collection_counts()
    logger.info("collections: %s", counts)
    if container.degraded:
        logger.warning("degraded subsystems: %s", list(container.degraded))

    yield

    logger.info("shutting down")
    app.state.container = None


settings = get_settings()

app = FastAPI(
    title="SHIA-DATA AI Engine",
    description="Internal retrieval and analysis engine. Consumed by the NestJS backend.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    # Kept enabled in every environment (behind the API key) because the
    # NestJS side generates its types from this document.
    openapi_url="/openapi.json",
)


@app.get("/api/v1/health", tags=["System"], response_model=HealthResponse)
def health_check(container: ServiceContainer = Depends(get_container)) -> HealthResponse:
    """
    Unauthenticated liveness + inventory.

    Deliberately open so orchestrator probes work, and deliberately cheap so it
    still answers while a heavy request is in flight.
    """
    index = container.rijal_index
    return HealthResponse(
        status="degraded" if container.degraded else "online",
        collections=container.collection_counts(),
        rijal_index_size=len(index) if index is not None else None,
        degraded=container.degraded,
    )


# Every data route requires the shared secret. /health above does not.
guarded = [Depends(require_api_key)]

app.include_router(search.router, dependencies=guarded)
app.include_router(chat.router, dependencies=guarded)
app.include_router(theology.router, dependencies=guarded)
app.include_router(rijal.router, dependencies=guarded)
app.include_router(hadith.router, dependencies=guarded)
app.include_router(ijtihad.router, dependencies=guarded)
# Storyteller is intentionally left untouched and unguarded-by-plan; it stays
# mounted but non-functional until the NestJS storyteller replaces it.
app.include_router(story.router, dependencies=guarded)


if __name__ == "__main__":
    logger.info("starting SHIA-DATA API on %s:%s", settings.host, settings.port)
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
