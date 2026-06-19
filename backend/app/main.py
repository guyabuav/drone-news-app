"""
FastAPI application for Drone News API.
Main entry point for the backend.
"""

import threading
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import requests
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import Base, engine, get_db, SessionLocal
from app.schemas import ArticleResponse, ArticlesPaginatedResponse, SyncResponse
from app.services import get_articles, sync_articles

logger = logging.getLogger(__name__)
sync_lock = threading.Lock()

def scheduled_sync():
    """Sync articles from News API (background job)"""
    with sync_lock:
        db = SessionLocal()
        try:
            result = sync_articles(db)
            logger.info(f"Scheduled sync completed: {result}")
        except Exception as e:
            logger.error(f"Scheduled sync failed: {e}")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    Base.metadata.create_all(bind=engine)

    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_sync, "interval", hours=1, id="sync_articles")
    scheduler.start()
    logger.info("Scheduled sync job started (runs every hour)")

    yield

    scheduler.shutdown()
    logger.info("Scheduled sync job stopped")


app = FastAPI(title="Drone News API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.get("/", response_model=dict)
def health_check():
    logger.info('Health check called')
    return {
        "status": "ok",
        "message": "Drone News API is running",
    }


@app.get("/articles", response_model=ArticlesPaginatedResponse)
def get_articles_endpoint(keyword: str | None = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    logger.info(f'Get articles called: keyword={keyword}, skip={skip}, limit={limit}')
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


@app.post("/articles/sync", response_model=SyncResponse)
@limiter.limit("1/5minutes")
def sync_articles_endpoint(request: Request, db: Session = Depends(get_db)):
    logger.info(f'Manual sync triggered from {request.client.host}')
    with sync_lock:
        try:
            result = sync_articles(db)
            logger.info(f'Manual sync completed successfully: {result}')
            return SyncResponse(**result)
        except RuntimeError as e:
            logger.error(f'Sync failed with RuntimeError: {e}')
            raise HTTPException(status_code=500, detail=str(e))
        except requests.exceptions.RequestException as e:
            logger.error(f'Sync failed with RequestException: {e}')
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch articles from News API: {str(e)}"
            )
        except Exception as e:
            logger.error(f'Sync failed with unexpected error: {e}', exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to sync articles: {str(e)}")
