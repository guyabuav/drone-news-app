from datetime import datetime, timezone


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
                "published_at": datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
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


def test_get_articles_with_keyword(client, db_session, monkeypatch):
    from app.schemas import ArticleBase
    from app.services import create_article

    article = ArticleBase(
        title="Drone delivery service",
        url="https://example.com/delivery",
        description="Fast drone delivery",
        published_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    create_article(db_session, article)

    response = client.get("/articles?keyword=delivery")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_get_articles_empty(client):
    response = client.get("/articles")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_get_articles_pagination(client, db_session, monkeypatch):
    from app.schemas import ArticleBase
    from app.services import create_article

    for i in range(5):
        article = ArticleBase(
            title=f"Article {i}",
            url=f"https://example.com/article-{i}",
            published_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        create_article(db_session, article)

    response = client.get("/articles?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["skip"] == 0
    assert data["limit"] == 2



