import logging
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Article
from app.news_client import fetch_drone_news
from app.schemas import ArticleBase

logger = logging.getLogger(__name__)


def get_articles(db: Session, keyword: Optional[str] = None, skip: int = 0, limit: int = 50) -> dict:
    query = db.query(Article)
    if keyword:
        logger.debug(f'Searching articles with keyword: {keyword}')
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

    logger.debug(f'Retrieved {len(items)} articles (total: {total}) with skip={skip}, limit={limit}')
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def create_article(db: Session, article_data: ArticleBase) -> tuple[Article, bool]:
    """Create article or return existing. Returns (article, is_new: bool)."""
    existing_article = db.query(Article).filter(Article.url == article_data.url).first()
    if existing_article:
        logger.debug(f'Article already exists: {article_data.url}')
        return existing_article, False

    logger.debug(f'Creating new article: {article_data.title}')
    article = Article(**article_data.model_dump())
    db.add(article)
    try:
        db.commit()
    except Exception as e:
        logger.error(f'Failed to create article: {e}', exc_info=True)
        db.rollback()
        raise
    db.refresh(article)
    logger.info(f'Article created successfully: {article.id} - {article.title}')
    return article, True


def sync_articles(db: Session) -> dict:
    logger.info('Starting article sync...')
    try:
        fetched_articles = fetch_drone_news()
    except Exception as e:
        logger.error(f'Failed to fetch articles from NewsAPI: {e}', exc_info=True)
        raise

    saved = 0
    duplicates = 0

    for article_payload in fetched_articles:
        article_data = ArticleBase(**article_payload)
        _, is_new = create_article(db, article_data)
        if is_new:
            saved += 1
        else:
            duplicates += 1

    result = {
        'fetched': len(fetched_articles),
        'saved': saved,
        'duplicates': duplicates,
    }
    logger.info(f'Sync completed: {result}')
    return result
