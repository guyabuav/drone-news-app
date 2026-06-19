from datetime import datetime, timezone

from app.models import Article
from app.schemas import ArticleBase
from app.services import create_article, get_articles, sync_articles


def test_create_article_and_get_articles(db_session):
    article = ArticleBase(
        title="Drone delivery advances",
        description="A new drone delivery test was successful.",
        content="The team completed the flight.",
        url="https://example.com/drone-delivery",
        author="Jane Doe",
        source_name="Drone Daily",
        published_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
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
            "published_at": datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
        },
        {
            "title": "Drone safety rules updated",
            "description": "FAA updates regulations.",
            "content": "Operators must comply with new guidelines.",
            "url": "https://example.com/drone-safety",
            "author": "Sam Flyer",
            "source_name": "FlightWatch",
            "published_at": datetime(2024, 1, 3, 9, 0, tzinfo=timezone.utc),
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


def test_create_duplicate_article(db_session):
    article1 = ArticleBase(
        title="Original article",
        url="https://example.com/article",
        description="First version",
        content="Content 1",
        author="Author 1",
        source_name="Source 1",
        published_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    article2 = ArticleBase(
        title="Updated article",
        url="https://example.com/article",  # Same URL
        description="Second version",
        content="Content 2",
        author="Author 2",
        source_name="Source 2",
        published_at=datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc),
    )

    saved1, is_new1 = create_article(db_session, article1)
    assert is_new1 is True
    assert saved1.title == "Original article"

    saved2, is_new2 = create_article(db_session, article2)
    assert is_new2 is False
    assert saved2.id == saved1.id
    assert saved2.title == "Original article"  # Not updated

    assert db_session.query(Article).count() == 1


def test_get_articles_with_wildcard_keyword(db_session):
    articles_data = [
        {
            "title": "Drone with % symbol in title",
            "url": "https://example.com/percent",
            "description": "Contains % wildcard character",
            "published_at": datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        },
        {
            "title": "Regular drone delivery service",
            "url": "https://example.com/delivery",
            "description": "Fast and reliable",
            "published_at": datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc),
        },
        {
            "title": "Advanced drone technology",
            "url": "https://example.com/technology",
            "description": "Next generation drones",
            "published_at": datetime(2024, 1, 3, 12, 0, tzinfo=timezone.utc),
        },
    ]

    for article_data in articles_data:
        article = ArticleBase(**article_data)
        create_article(db_session, article)

    # Search for literal "%" - should only match article with % in title
    result = get_articles(db_session, keyword="%")
    assert result["total"] == 1
    assert result["items"][0].title == "Drone with % symbol in title"

    # Search for "_" - should match nothing (no underscore in titles)
    result = get_articles(db_session, keyword="_")
    assert result["total"] == 0

    # Search for "drone" - should match all 3 articles
    result = get_articles(db_session, keyword="drone")
    assert result["total"] == 3


def test_get_articles_empty_database(db_session):
    result = get_articles(db_session)
    assert result["total"] == 0
    assert len(result["items"]) == 0
    assert result["skip"] == 0
    assert result["limit"] == 50


def test_get_articles_pagination(db_session):
    for i in range(10):
        article = ArticleBase(
            title=f"Article {i}",
            url=f"https://example.com/article-{i}",
            published_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        create_article(db_session, article)

    page1 = get_articles(db_session, skip=0, limit=3)
    assert page1["total"] == 10
    assert len(page1["items"]) == 3
    assert page1["skip"] == 0
    assert page1["limit"] == 3

    page2 = get_articles(db_session, skip=3, limit=3)
    assert page2["total"] == 10
    assert len(page2["items"]) == 3
    assert page2["skip"] == 3

    last_page = get_articles(db_session, skip=9, limit=3)
    assert len(last_page["items"]) == 1


def test_sync_articles_missing_api_key(db_session, monkeypatch):
    monkeypatch.delenv("NEWS_API_KEY", raising=False)

    try:
        sync_articles(db_session)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "NEWS_API_KEY" in str(e)


def test_sync_articles_api_failure(db_session, monkeypatch):
    def fake_fetch_error():
        import requests
        raise requests.exceptions.ConnectionError("API unreachable")

    monkeypatch.setattr("app.services.fetch_drone_news", fake_fetch_error)

    try:
        sync_articles(db_session)
        assert False, "Should have raised RequestException"
    except Exception as e:
        assert "ConnectionError" in str(type(e))


