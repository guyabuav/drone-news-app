"""
FastAPI application for Drone News API.
Main entry point for the backend.
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import requests

from app.database import Base, engine, get_db
from app.schemas import ArticleResponse
from app.services import get_articles, sync_articles

app = FastAPI(title="Drone News API", version="0.1.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/", response_model=dict)
def health_check():
    return {
        "status": "ok",
        "message": "Drone News API is running",
    }


@app.get("/articles", response_model=list[ArticleResponse])
def get_articles_endpoint(keyword: str | None = None, db: Session = Depends(get_db)):
    return get_articles(db, keyword)


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
