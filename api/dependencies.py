"""
FastAPI dependency providers.

This is the file architecture.md always specified but that never existed --
auth, shared dependency wiring, and the boundary between routes and services.
"""

import secrets
from typing import Annotated, Any, Callable

from fastapi import Depends, Header, HTTPException, Request, status

from core.container import ServiceContainer


def get_container(request: Request) -> ServiceContainer:
    container = getattr(request.app.state, "container", None)
    if container is None:  # pragma: no cover - only if lifespan didn't run
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service container not initialised",
        )
    return container


ContainerDep = Annotated[ServiceContainer, Depends(get_container)]


async def require_api_key(
    container: ContainerDep,
    x_internal_api_key: Annotated[str | None, Header(alias="X-Internal-API-Key")] = None,
) -> None:
    """
    Shared-secret guard for the NestJS -> Python hop.

    compare_digest rather than `!=` because a plain string comparison
    short-circuits on the first differing byte and leaks the secret one
    character at a time to anyone who can measure response latency.
    """
    expected = container.settings.internal_api_key
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="INTERNAL_API_KEY is not configured on this server",
        )
    if x_internal_api_key is None or not secrets.compare_digest(
        x_internal_api_key, expected
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Internal-API-Key",
        )


def _require_service(name: str) -> Callable[..., Any]:
    """Build a dependency that 503s with a reason when a subsystem is degraded."""

    def dependency(container: ContainerDep) -> Any:
        service = getattr(container, name, None)
        if service is None:
            reason = container.degraded.get(name, "unknown reason")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"The '{name}' subsystem is unavailable: {reason}",
            )
        return service

    return dependency


get_theology_service = _require_service("theology")
get_rijal_service = _require_service("rijal")
get_hadith_service = _require_service("hadith")
get_ijtihad_service = _require_service("ijtihad")
get_conflict_service = _require_service("conflict")
