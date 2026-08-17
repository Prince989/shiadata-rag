"""
Guards against re-introducing the event-loop-freezing bug: six route handlers
used to be `async def` while calling fully blocking LLM/ChromaDB code with no
await, so one heavy request froze the entire process -- /health included.

FastAPI runs plain `def` handlers in a threadpool, which is correct for
blocking I/O. Every route in this service must therefore be a plain function,
never a coroutine function.
"""

import inspect

from fastapi.routing import APIRoute

from main import app


def _all_api_routes(routes) -> list[APIRoute]:
    """
    Recursively flatten every APIRoute out of app.routes.

    Newer FastAPI/Starlette wraps included routers in an internal container
    (currently `_IncludedRouter`, reached via `.original_router`) rather than
    exposing their routes at the top level of `app.routes` -- a naive
    `isinstance(r, APIRoute)` filter over `app.routes` directly finds only
    routes declared straight on `app`, silently missing everything mounted
    via `include_router`.
    """
    found: list[APIRoute] = []
    for route in routes:
        if isinstance(route, APIRoute):
            found.append(route)
        elif hasattr(route, "original_router"):
            found.extend(_all_api_routes(route.original_router.routes))
        elif hasattr(route, "routes"):
            found.extend(_all_api_routes(route.routes))
    return found


def test_no_route_handler_is_a_coroutine_function():
    routes = _all_api_routes(app.routes)
    assert routes, "route discovery found nothing -- the walk above is broken"

    offenders = [
        route.path for route in routes if inspect.iscoroutinefunction(route.endpoint)
    ]

    assert not offenders, (
        f"These routes are `async def` but this service's handlers all call "
        f"blocking code: {offenders}. Either make them plain `def` (FastAPI "
        f"threadpools it) or genuinely await everything inside."
    )
