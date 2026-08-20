from fastapi import APIRouter, HTTPException, Query, status
from typing import List
import logging

from app.modules.market_data.service import MarketDataService
from app.modules.market_data.schemas import (
    NormalizedTicker,
    AssetInfo,
    MarketOverviewResponse,
    CandleResponse,
)
from app.modules.market_data.exceptions import (
    InvalidAssetError,
    InvalidTimeframeError,
    ProviderUnavailableError,
    ProviderTimeoutError,
)

router = APIRouter()
market_service = MarketDataService()

@router.get("/overview", response_model=MarketOverviewResponse, summary="Get Market Overview Tickers")
async def get_market_overview():
    """Fetch normalized live market overview tickers for core supported assets (BTC, ETH, SOL)."""
    try:
        return await market_service.get_market_overview()
    except ProviderUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error in market overview endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch market overview")

@router.get("/assets", response_model=List[AssetInfo], summary="Get Supported Assets List")
async def get_supported_assets():
    """Get list of supported market assets with metadata and provider mappings."""
    try:
        return await market_service.get_supported_assets()
    except Exception as e:
        logging.error(f"Error fetching supported assets: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch supported assets")

@router.get("/{symbol}/candles", response_model=CandleResponse, summary="Get OHLCV Candles for Asset")
async def get_asset_candles(
    symbol: str,
    timeframe: str = Query("1H", description="Timeframe: 1m, 5m, 15m, 1H, 4H, 1D"),
    limit: int = Query(100, ge=1, le=300, description="Max candles limit (1..300)")
):
    """Fetch normalized OHLCV candle history for a supported symbol."""
    try:
        return await market_service.get_candles(symbol, timeframe, limit)
    except InvalidAssetError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidTimeframeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ProviderUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error fetching candles for {symbol}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch candles for {symbol}")

@router.get("/{symbol}", response_model=NormalizedTicker, summary="Get Ticker for Single Asset")
async def get_asset_ticker(symbol: str):
    """Fetch normalized ticker metrics for a single symbol (e.g. BTC, ETH, SOL)."""
    try:
        return await market_service.get_ticker(symbol)
    except InvalidAssetError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ProviderUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error fetching ticker for {symbol}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch ticker for {symbol}")
