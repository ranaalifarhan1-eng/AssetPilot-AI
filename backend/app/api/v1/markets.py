from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
import logging

from app.modules.market_data.service import MarketDataService
from app.modules.market_data.schemas import (
    NormalizedTicker,
    AssetInfo,
    MarketOverviewResponse,
    CandleResponse,
    NormalizedEquityQuote,
    NormalizedTokenizedEquityQuote,
    EquityComparisonResponse,
)
from app.modules.market_data.exceptions import (
    InvalidAssetError,
    InvalidTimeframeError,
    ProviderUnavailableError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)

router = APIRouter()
market_service = MarketDataService()

@router.get("/overview", response_model=MarketOverviewResponse, summary="Get Market Overview Tickers")
async def get_market_overview():
    """Fetch normalized live market overview tickers for core supported crypto assets (BTC, ETH, SOL)."""
    try:
        return await market_service.get_market_overview()
    except ProviderUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in market overview endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch market overview")

@router.get("/assets", response_model=List[AssetInfo], summary="Get Supported Assets Catalog")
async def get_supported_assets(
    type: Optional[str] = Query(None, description="Filter category: crypto, equity, tokenized_equity, etf, index_reference"),
    query: Optional[str] = Query(None, description="Search query by symbol or name")
):
    """Get multi-asset catalog across Crypto, US Equities, and OKX Tokenized Equities with metadata."""
    try:
        return await market_service.get_supported_assets(type_filter=type, query=query)
    except Exception as e:
        logger.error(f"Error fetching supported assets: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch supported assets")

# --- Traditional Equities Endpoints ---
@router.get("/equities", response_model=List[NormalizedEquityQuote], summary="Get Traditional Equities Quotes")
async def get_equities():
    """Get quotes for the supported US traditional equities watch universe."""
    try:
        return await market_service.get_equities()
    except Exception as e:
        logger.error(f"Error fetching equities quotes: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch equity quotes")

@router.get("/equities/{symbol}", response_model=NormalizedEquityQuote, summary="Get Quote for Single Equity")
async def get_equity_quote(symbol: str):
    """Fetch quote for a specific US equity symbol (e.g. AAPL, GOOGL, NVDA)."""
    try:
        return await market_service.get_equity_quote(symbol)
    except InvalidAssetError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching equity quote for {symbol}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch quote for {symbol}")

# --- OKX Tokenized Equities Endpoints ---
@router.get("/tokenized-equities", response_model=List[NormalizedTokenizedEquityQuote], summary="Get OKX Tokenized Equities Quotes")
async def get_tokenized_equities():
    """Get live quotes for dynamically discovered OKX tokenized stock instruments (xStocks)."""
    try:
        return await market_service.get_tokenized_equities()
    except Exception as e:
        logger.error(f"Error fetching tokenized equities: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch tokenized equity quotes")

@router.get("/tokenized-equities/{symbol}", response_model=NormalizedTokenizedEquityQuote, summary="Get Quote for Single Tokenized Equity")
async def get_tokenized_equity_quote(symbol: str):
    """Fetch quote for a specific OKX tokenized stock (e.g. xGOOGL or GOOGL)."""
    try:
        return await market_service.get_tokenized_equity_quote(symbol)
    except InvalidAssetError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching tokenized quote for {symbol}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch tokenized quote for {symbol}")

# --- Price Comparison Endpoint ---
@router.get("/equity-comparison/{underlying_symbol}", response_model=EquityComparisonResponse, summary="Compare Equity vs OKX Tokenized Price")
async def get_equity_comparison(underlying_symbol: str):
    """Compare a traditional US equity reference price with its OKX tokenized counterpart if listed."""
    try:
        return await market_service.compare_equity(underlying_symbol)
    except InvalidAssetError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing equity for {underlying_symbol}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to compare equity for {underlying_symbol}")

# --- Candle and Generic Ticker Endpoints ---
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
        logger.error(f"Unexpected error fetching candles for {symbol}: {e}")
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
        logger.error(f"Unexpected error fetching ticker for {symbol}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch ticker for {symbol}")
