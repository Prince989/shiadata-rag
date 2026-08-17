"""
Guards against re-introducing endpoints with no response_model: three routes
used to return bare dicts with no declared shape (/hadith/search,
/grand-ijtihad, /conflict-resolution), which made them invisible to codegen --
any NestJS client generated from this OpenAPI document would have typed them
as `any`.
"""


def test_every_operation_declares_a_response_schema(client):
    spec = client.get("/openapi.json").json()

    missing = []
    for path, operations in spec["paths"].items():
        for method, op in operations.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH"):
                continue
            responses = op.get("responses", {})
            ok = responses.get("200") or responses.get("201")
            has_schema = bool(ok and ok.get("content"))
            if not has_schema:
                missing.append(f"{method.upper()} {path}")

    assert not missing, f"Endpoints with no response schema: {missing}"
