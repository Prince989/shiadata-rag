def test_missing_key_is_rejected(client):
    response = client.post("/api/v1/search", json={"query": "x", "collection": "hadith"})
    assert response.status_code == 401


def test_wrong_key_is_rejected(client):
    response = client.post(
        "/api/v1/search",
        json={"query": "x", "collection": "hadith"},
        headers={"X-Internal-API-Key": "not-the-right-key"},
    )
    assert response.status_code == 401


def test_correct_key_is_accepted(client, auth_headers):
    response = client.post(
        "/api/v1/search",
        json={"query": "x", "collection": "hadith"},
        headers=auth_headers,
    )
    assert response.status_code == 200


def test_health_is_never_guarded(client):
    # /health must stay reachable without a key, even under a bad key.
    response = client.get(
        "/api/v1/health", headers={"X-Internal-API-Key": "garbage"}
    )
    assert response.status_code == 200
