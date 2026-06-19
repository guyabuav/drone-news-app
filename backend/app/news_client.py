"""
News client for fetching drone-related news from NewsAPI.org.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)
NEWS_API_BASE_URL = 'https://newsapi.org/v2/everything'


def fetch_drone_news() -> List[dict]:
    """
    Fetch drone-related news articles from News API.

    Raises:
        RuntimeError: If NEWS_API_KEY is not configured.
        requests.RequestException: If the API request fails.
    """
    api_key = os.getenv('NEWS_API_KEY', '').strip()
    if not api_key:
        logger.error('NEWS_API_KEY is missing')
        raise RuntimeError(
            'NEWS_API_KEY is missing. Please create a .env file based on .env.example.'
        )

    params = {
        'q': 'drone OR drones',
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 100,
        'apiKey': api_key,
    }

    logger.info('Fetching drone news from NewsAPI...')
    try:
        response = requests.get(NEWS_API_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to fetch from NewsAPI: {e}')
        raise

    data = response.json()
    if not isinstance(data, dict) or not isinstance(data.get('articles'), list):
        logger.error(f'Unexpected NewsAPI response format: {data}')
        raise RuntimeError(f'Unexpected News API response format: {data}')

    articles = []
    for article in data['articles']:
        normalized_article = _normalize_article(article)
        if normalized_article:
            articles.append(normalized_article)

    logger.info(f'Fetched {len(articles)} drone articles from NewsAPI')
    return articles


def _normalize_article(article: dict) -> Optional[dict]:
    title = article.get('title')
    url = article.get('url')
    if not title or not isinstance(title, str):
        return None
    if not url or not isinstance(url, str):
        return None

    title = title.strip()
    url = url.strip()
    if not title or not url:
        return None

    description = article.get('description')
    description = description.strip() if isinstance(description, str) and description else None

    content = article.get('content')
    content = content.strip() if isinstance(content, str) and content else None

    author = article.get('author')
    author = author.strip() if isinstance(author, str) and author else None

    source_name = None
    source = article.get('source')
    if isinstance(source, dict):
        source_name = source.get('name')
        source_name = source_name.strip() if isinstance(source_name, str) and source_name else None

    return {
        'title': title,
        'description': description,
        'content': content,
        'url': url,
        'author': author,
        'source_name': source_name,
        'published_at': _parse_datetime(article.get('publishedAt')),
    }


def _parse_datetime(date_string: Optional[str]) -> Optional[datetime]:
    if not date_string or not isinstance(date_string, str):
        return None

    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None
