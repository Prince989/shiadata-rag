def test_health_requires_no_auth(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("online", "degraded")
    assert "collections" in body
