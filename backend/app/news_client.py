"""
News client for fetching drone-related news from NewsAPI.org.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

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
        raise RuntimeError(
            'NEWS_API_KEY is missing. Please create a .env file based on .env.example.'
        )

    params = {
        'q': 'drone OR drones',
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 50,
        'apiKey': api_key,
    }

    response = requests.get(NEWS_API_BASE_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, dict) or not isinstance(data.get('articles'), list):
        raise RuntimeError(f'Unexpected News API response format: {data}')

    articles = []
    for article in data['articles']:
        normalized_article = _normalize_article(article)
        if normalized_article:
            articles.append(normalized_article)

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
