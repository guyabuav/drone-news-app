from datetime import datetime

from app.models import Article
from app.schemas import ArticleCreate
from app.services import create_article, get_articles, sync_articles


def test_create_article_and_get_articles(db_session):
    article = ArticleCreate(
        title="Drone delivery advances",
        description="A new drone delivery test was successful.",
        content="The team completed the flight.",
        url="https://example.com/drone-delivery",
        author="Jane Doe",
        source_name="Drone Daily",
        published_at=datetime(2024, 1, 1, 12, 0),
    )

    saved_article, is_new = create_article(db_session, article)
    assert is_new is True
    assert saved_article.id is not None
    assert saved_article.url == article.url

    result = get_articles(db_session, keyword="delivery")
    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0].title == article.title


def test_sync_articles_skips_duplicates(db_session, monkeypatch):
    sample_articles = [
        {
            "title": "Drone racing returns",
            "description": "A new racing league has launched.",
            "content": "The season will start next month.",
            "url": "https://example.com/drone-racing",
            "author": "Alex Pilot",
            "source_name": "Aero News",
            "published_at": "2024-01-02T10:00:00Z",
        },
        {
            "title": "Drone safety rules updated",
            "description": "FAA updates regulations.",
            "content": "Operators must comply with new guidelines.",
            "url": "https://example.com/drone-safety",
            "author": "Sam Flyer",
            "source_name": "FlightWatch",
            "published_at": "2024-01-03T09:00:00Z",
        },
    ]

    def fake_fetch():
        return sample_articles + [sample_articles[0]]

    monkeypatch.setattr("app.services.fetch_drone_news", fake_fetch)

    result = sync_articles(db_session)

    assert result["fetched"] == 3
    assert result["saved"] == 2
    assert result["duplicates"] == 1
    assert db_session.query(Article).count() == 2
