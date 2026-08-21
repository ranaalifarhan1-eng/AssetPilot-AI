from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional
import logging

from app.modules.news_intelligence.service import NewsService
from app.modules.news_intelligence.schemas import (
    NewsListResponse,
    NewsStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()
news_service = NewsService()

@router.get("", response_model=NewsListResponse, summary="Get Normalized Financial News Feed")
async def get_news_feed(
    category: Optional[str] = Query(None, description="Filter by category (e.g. 'crypto', 'company', 'macro', 'regulation', 'earnings')"),
    asset: Optional[str] = Query(None, description="Filter by asset symbol (e.g. 'BTC', 'NVDA', 'AAPL')"),
    source: Optional[str] = Query(None, description="Filter by provider source name"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment ('positive', 'neutral', 'negative', 'mixed')"),
    impact: Optional[str] = Query(None, description="Filter by impact level ('high', 'medium', 'low')"),
    portfolio_only: bool = Query(False, description="Filter to only stories matching held OKX portfolio assets"),
    limit: int = Query(50, ge=1, le=100, description="Max number of articles to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """Retrieve normalized, deduplicated financial news with asset mapping and conservative sentiment metadata."""
    try:
        return await news_service.get_news(
            category=category,
            asset=asset,
            source=source,
            sentiment=sentiment,
            impact=impact,
            portfolio_only=portfolio_only,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error fetching news feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve financial news"
        )

@router.get("/assets/{symbol}", response_model=NewsListResponse, summary="Get News for Specific Asset")
async def get_news_for_asset(
    symbol: str,
    limit: int = Query(20, ge=1, le=50, description="Max number of articles to return")
):
    """Retrieve news articles specifically mapped to a target crypto or equity symbol."""
    try:
        return await news_service.get_news_for_asset(symbol=symbol, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching news for asset {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve news for asset '{symbol}'"
        )

@router.get("/portfolio", response_model=NewsListResponse, summary="Get News Matching Held Portfolio Assets")
async def get_portfolio_news(
    limit: int = Query(20, ge=1, le=50, description="Max number of articles to return")
):
    """Retrieve news articles that directly reference assets in the user's connected OKX portfolio."""
    try:
        return await news_service.get_portfolio_news(limit=limit)
    except Exception as e:
        logger.error(f"Error fetching portfolio news: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio news"
        )

@router.get("/status", response_model=NewsStatusResponse, summary="Get News Providers & Collection Status")
async def get_news_status():
    """Get metadata regarding active news providers, cached count, and collection timestamps (never exposes secrets)."""
    try:
        return await news_service.get_status()
    except Exception as e:
        logger.error(f"Error fetching news status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve news status"
        )

@router.post("/refresh", summary="Trigger On-Demand News Collection")
async def refresh_news_collection():
    """Manually refresh news collection across all configured providers with server-side cooldown protection."""
    try:
        count, cooldown_active = await news_service.refresh_news(force=False)
        return {
            "status": "success",
            "collected_articles_count": count,
            "cooldown_active": cooldown_active,
            "message": "Cooldown active; returned existing cached collection." if cooldown_active else "Fresh collection complete."
        }
    except Exception as e:
        logger.error(f"Error refreshing news: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh news collection"
        )
