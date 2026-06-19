from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict


class ArticleBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    author: Optional[str] = None
    source_name: Optional[str] = None
    published_at: Optional[datetime] = None


class ArticleResponse(ArticleBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticlesPaginatedResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    skip: int
    limit: int


class SyncResponse(BaseModel):
    fetched: int
    saved: int
    duplicates: int
