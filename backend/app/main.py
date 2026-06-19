"""
FastAPI application for Drone News API.
Main entry point for the backend.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
from dotenv import load_dotenv

from app.database import Base, engine, get_db
from app.schemas import ArticleResponse, ArticlesPaginatedResponse
from app.services import get_articles, sync_articles


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Drone News API", version="0.1.0", lifespan=lifespan)


@app.get("/", response_model=dict)
def health_check():
    return {
        "status": "ok",
        "message": "Drone News API is running",
    }


@app.get("/articles", response_model=ArticlesPaginatedResponse)
def get_articles_endpoint(keyword: str | None = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 100:
        limit = 50
    result = get_articles(db, keyword, skip, limit)
    return ArticlesPaginatedResponse(
        items=result["items"],
        total=result["total"],
        skip=result["skip"],
        limit=result["limit"],
    )


@app.post("/articles/sync", response_model=dict)
def sync_articles_endpoint(db: Session = Depends(get_db)):
    try:
        return sync_articles(db)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch articles from News API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync articles: {str(e)}")
