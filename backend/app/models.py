from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(500), nullable=False, unique=True, index=True)
    author = Column(String(255), nullable=True)
    source_name = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
