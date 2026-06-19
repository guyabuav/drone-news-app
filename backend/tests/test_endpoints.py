def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Drone News API is running",
    }


def test_sync_endpoint(client, monkeypatch):
    def fake_fetch():
        return [
            {
                "title": "Drone test article",
                "description": "Test description",
                "content": "Test content",
                "url": "https://example.com/test-drone",
                "author": "Test Author",
                "source_name": "Test Source",
                "published_at": "2024-01-01T12:00:00Z",
            }
        ]

    monkeypatch.setattr("app.services.fetch_drone_news", fake_fetch)

    response = client.post("/articles/sync")
    assert response.status_code == 200
    data = response.json()
    assert data["fetched"] == 1
    assert data["saved"] == 1
    assert data["duplicates"] == 0

    articles_response = client.get("/articles")
    assert articles_response.status_code == 200
    data = articles_response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
