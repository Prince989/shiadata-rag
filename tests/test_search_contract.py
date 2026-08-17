"""
Guards the two gotchas the generic search endpoint hits that the old
per-collection routes never did: multi-key filters need $and wrapping (the
old code only ever passed one filter key), and metadata must survive the
response (the old hadith_service discarded it entirely).
"""


def test_single_filter_key_passed_through(client, auth_headers, fake_container):
    store = fake_container.stores["hadith"]
    client.post(
        "/api/v1/search",
        json={"query": "x", "collection": "hadith", "filters": {"domain": "history"}},
        headers=auth_headers,
    )
    assert store.last_filter == {"domain": "history"}


def test_multi_key_filter_is_and_wrapped(client, auth_headers, fake_container):
    store = fake_container.stores["hadith"]
    client.post(
        "/api/v1/search",
        json={
            "query": "x",
            "collection": "hadith",
            "filters": {"domain": "history", "language": "ar"},
        },
        headers=auth_headers,
    )
    assert store.last_filter == {
        "$and": [{"domain": "history"}, {"language": "ar"}]
    }


def test_unknown_collection_is_404(client, auth_headers):
    response = client.post(
        "/api/v1/search",
        json={"query": "x", "collection": "nonexistent"},
        headers=auth_headers,
    )
    # Rejected by the Literal enum in the request schema before it ever
    # reaches the collection lookup.
    assert response.status_code == 422


def test_top_k_over_limit_is_rejected(client, auth_headers):
    response = client.post(
        "/api/v1/search",
        json={"query": "x", "collection": "hadith", "top_k": 999},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_response_carries_full_metadata(client, auth_headers):
    response = client.post(
        "/api/v1/search",
        json={"query": "x", "collection": "hadith"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    doc = response.json()["documents"][0]
    assert doc["book_title"] == "Fake Book"
    assert doc["domain"] == "history"
    assert "distance" in doc


def test_mmr_search_type_used(client, auth_headers, fake_container):
    store = fake_container.stores["hadith"]
    client.post(
        "/api/v1/search",
        json={"query": "x", "collection": "hadith", "search_type": "mmr"},
        headers=auth_headers,
    )
    assert store.last_search_type == "mmr"
