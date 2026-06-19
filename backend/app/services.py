from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Article
from app.news_client import fetch_drone_news
from app.schemas import ArticleCreate

def get_articles(db: Session, keyword: Optional[str] = None, skip: int = 0, limit: int = 50) -> dict:
    query = db.query(Article)
    if keyword:
        keyword_escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{keyword_escaped}%"
        query = query.filter(
            or_(
                Article.title.ilike(pattern, escape="\\"),
                Article.description.ilike(pattern, escape="\\"),
                Article.content.ilike(pattern, escape="\\"),
            )
        )

    total = query.count()
    items = query.order_by(Article.published_at.desc().nullslast(), Article.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def create_article(db: Session, article_data: ArticleCreate) -> tuple[Article, bool]:
    """Create article or return existing. Returns (article, is_new: bool)."""
    existing_article = db.query(Article).filter(Article.url == article_data.url).first()
    if existing_article:
        return existing_article, False

    article = Article(**article_data.model_dump())
    db.add(article)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(article)
    return article, True


def sync_articles(db: Session) -> dict:
    fetched_articles = fetch_drone_news()
    saved = 0
    duplicates = 0

    for article_payload in fetched_articles:
        article_data = ArticleCreate(**article_payload)
        _, is_new = create_article(db, article_data)
        if is_new:
            saved += 1
        else:
            duplicates += 1

    return {
        'fetched': len(fetched_articles),
        'saved': saved,
        'duplicates': duplicates,
    }
