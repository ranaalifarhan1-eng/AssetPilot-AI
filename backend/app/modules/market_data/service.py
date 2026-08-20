from typing import List, Optional
from datetime import datetime, timezone
import logging

from app.modules.market_data.base import BaseMarketDataProvider
from app.modules.market_data.okx_provider import OKXMarketDataProvider
from app.modules.market_data.cache import global_cache, MarketDataCache
from app.modules.market_data.schemas import (
    NormalizedTicker,
    NormalizedCandle,
    AssetInfo,
    MarketOverviewResponse,
    CandleResponse,
)

logger = logging.getLogger(__name__)

class MarketDataService:
    def __init__(self, provider: Optional[BaseMarketDataProvider] = None, cache: Optional[MarketDataCache] = None):
        self.provider = provider or OKXMarketDataProvider()
        self.cache = cache or global_cache

    async def get_supported_assets(self) -> List[AssetInfo]:
        return await self.provider.get_supported_assets()

    async def get_ticker(self, symbol: str) -> NormalizedTicker:
        symbol_upper = symbol.upper()
        cache_key = f"ticker:{symbol_upper}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        ticker = await self.provider.get_ticker(symbol_upper)
        await self.cache.set(cache_key, ticker, ttl=10.0)
        return ticker

    async def get_market_overview(self) -> MarketOverviewResponse:
        cache_key = "overview"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        supported = await self.get_supported_assets()
        symbols = [asset.symbol for asset in supported]
        tickers = await self.provider.get_tickers(symbols)

        response = MarketOverviewResponse(
            updated_at=datetime.now(timezone.utc),
            provider=self.provider.provider_name,
            tickers=tickers
        )
        await self.cache.set(cache_key, response, ttl=10.0)
        return response

    async def get_candles(self, symbol: str, timeframe: str = "1H", limit: int = 100) -> CandleResponse:
        symbol_upper = symbol.upper()
        cache_key = f"candles:{symbol_upper}:{timeframe}:{limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        candles = await self.provider.get_candles(symbol_upper, timeframe, limit)
        response = CandleResponse(
            symbol=symbol_upper,
            timeframe=timeframe,
            provider=self.provider.provider_name,
            candles=candles
        )
        await self.cache.set(cache_key, response, ttl=30.0)
        return response
