from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Article
from app.news_client import fetch_drone_news
from app.schemas import ArticleCreate


def get_articles(db: Session, keyword: Optional[str] = None) -> List[Article]:
    query = db.query(Article)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Article.title.ilike(pattern),
                Article.description.ilike(pattern),
                Article.content.ilike(pattern),
            )
        )

    return query.order_by(Article.published_at.desc().nullslast(), Article.created_at.desc()).all()


def create_article(db: Session, article_data: ArticleCreate) -> Article:
    existing_article = db.query(Article).filter(Article.url == article_data.url).first()
    if existing_article:
        return existing_article

    article = Article(**article_data.model_dump())
    db.add(article)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(article)
    return article


def sync_articles(db: Session) -> dict:
    fetched_articles = fetch_drone_news()
    saved = 0
    duplicates = 0

    for article_payload in fetched_articles:
        article_data = ArticleCreate(**article_payload)
        existing_article = db.query(Article).filter(Article.url == article_data.url).first()
        if existing_article:
            duplicates += 1
            continue

        create_article(db, article_data)
        saved += 1

    return {
        'fetched': len(fetched_articles),
        'saved': saved,
        'duplicates': duplicates,
    }
