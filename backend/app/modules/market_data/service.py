import logging
import asyncio
from typing import List, Optional, Dict
from datetime import datetime, timezone
from decimal import Decimal

from app.modules.market_data.base import BaseMarketDataProvider
from app.modules.market_data.okx_provider import OKXMarketDataProvider
from app.modules.market_data.equity_base import BaseEquityMarketDataProvider
from app.modules.market_data.finnhub_provider import FinnhubEquityProvider, SUPPORTED_EQUITIES_MAP
from app.modules.market_data.okx_tokenized import OKXTokenizedStocksProvider, RECOGNIZED_UNDERLYING_MAP
from app.modules.market_data.cache import global_cache, MarketDataCache
from app.modules.market_data.schemas import (
    NormalizedTicker,
    NormalizedCandle,
    AssetInfo,
    MarketOverviewResponse,
    CandleResponse,
    NormalizedEquityQuote,
    NormalizedTokenizedEquityQuote,
    EquityComparisonResponse,
    AssetCategory,
)
from app.modules.market_data.exceptions import InvalidAssetError

logger = logging.getLogger(__name__)

class MarketDataService:
    def __init__(
        self,
        crypto_provider: Optional[BaseMarketDataProvider] = None,
        equity_provider: Optional[BaseEquityMarketDataProvider] = None,
        tokenized_provider: Optional[OKXTokenizedStocksProvider] = None,
        cache: Optional[MarketDataCache] = None,
    ):
        self.crypto_provider = crypto_provider or OKXMarketDataProvider()
        self.equity_provider = equity_provider or FinnhubEquityProvider()
        self.tokenized_provider = tokenized_provider or OKXTokenizedStocksProvider()
        self.cache = cache or global_cache

    async def get_supported_assets(self, type_filter: Optional[str] = None, query: Optional[str] = None) -> List[AssetInfo]:
        """Return combined assets catalog with optional type and text query filtering"""
        cache_key = f"assets_catalog:{type_filter or 'all'}:{query or 'all'}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Concurrently gather assets across providers
        crypto_task = self.crypto_provider.get_supported_assets()
        equity_task = self.equity_provider.get_supported_equities()
        tokenized_task = self.tokenized_provider.discover_tokenized_instruments()

        crypto_assets, equity_assets, tokenized_assets = await asyncio.gather(
            crypto_task, equity_task, tokenized_task, return_exceptions=True
        )

        all_assets: List[AssetInfo] = []
        if isinstance(crypto_assets, list):
            all_assets.extend(crypto_assets)
        if isinstance(equity_assets, list):
            all_assets.extend(equity_assets)
        if isinstance(tokenized_assets, list):
            all_assets.extend(tokenized_assets)

        # Apply category filter
        if type_filter:
            tf_lower = type_filter.lower()
            all_assets = [a for a in all_assets if a.category.lower() == tf_lower]

        # Apply query filter
        if query:
            q_lower = query.lower()
            all_assets = [
                a for a in all_assets
                if q_lower in a.symbol.lower()
                or q_lower in a.name.lower()
                or (a.underlying_symbol and q_lower in a.underlying_symbol.lower())
            ]

        await self.cache.set(cache_key, all_assets, ttl=30.0)
        return all_assets

    async def get_ticker(self, symbol: str) -> NormalizedTicker:
        symbol_upper = symbol.upper()
        cache_key = f"ticker:{symbol_upper}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        ticker = await self.crypto_provider.get_ticker(symbol_upper)
        await self.cache.set(cache_key, ticker, ttl=10.0)
        return ticker

    async def get_market_overview(self) -> MarketOverviewResponse:
        cache_key = "overview"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        supported = await self.crypto_provider.get_supported_assets()
        symbols = [asset.symbol for asset in supported]
        tickers = await self.crypto_provider.get_tickers(symbols)

        response = MarketOverviewResponse(
            updated_at=datetime.now(timezone.utc),
            provider=self.crypto_provider.provider_name,
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

        if symbol_upper in SUPPORTED_EQUITIES_MAP:
            candles = await self.equity_provider.get_candles(symbol_upper, timeframe, limit)
            provider_name = self.equity_provider.provider_name
        else:
            candles = await self.crypto_provider.get_candles(symbol_upper, timeframe, limit)
            provider_name = self.crypto_provider.provider_name

        response = CandleResponse(
            symbol=symbol_upper,
            timeframe=timeframe,
            provider=provider_name,
            candles=candles
        )
        await self.cache.set(cache_key, response, ttl=30.0)
        return response

    # --- Traditional Equity Methods ---
    async def get_equities(self) -> List[NormalizedEquityQuote]:
        cache_key = "equities_quotes"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        symbols = list(SUPPORTED_EQUITIES_MAP.keys())
        quotes = await self.equity_provider.get_quotes(symbols)
        await self.cache.set(cache_key, quotes, ttl=30.0)
        return quotes

    async def get_equity_quote(self, symbol: str) -> NormalizedEquityQuote:
        sym_upper = symbol.upper()
        cache_key = f"equity_quote:{sym_upper}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        quote = await self.equity_provider.get_quote(sym_upper)
        await self.cache.set(cache_key, quote, ttl=30.0)
        return quote

    # --- OKX Tokenized Equity Methods ---
    async def get_tokenized_equities(self) -> List[NormalizedTokenizedEquityQuote]:
        cache_key = "tokenized_equities_quotes"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        quotes = await self.tokenized_provider.get_tokenized_quotes()
        await self.cache.set(cache_key, quotes, ttl=20.0)
        return quotes

    async def get_tokenized_equity_quote(self, symbol: str) -> NormalizedTokenizedEquityQuote:
        clean_sym = symbol.upper()
        cache_key = f"tokenized_quote:{clean_sym}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        quote = await self.tokenized_provider.get_tokenized_quote(clean_sym)
        await self.cache.set(cache_key, quote, ttl=20.0)
        return quote

    # --- Equity vs Tokenized Price Comparison ---
    async def compare_equity(self, underlying_symbol: str) -> EquityComparisonResponse:
        sym_upper = underlying_symbol.upper()
        if sym_upper.startswith("X") and sym_upper[1:] in RECOGNIZED_UNDERLYING_MAP:
            sym_upper = sym_upper[1:]

        if sym_upper not in SUPPORTED_EQUITIES_MAP and sym_upper not in RECOGNIZED_UNDERLYING_MAP:
            raise InvalidAssetError(underlying_symbol)

        cache_key = f"equity_comparison:{sym_upper}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        comp_name = RECOGNIZED_UNDERLYING_MAP.get(sym_upper, f"{sym_upper} Corporation")

        # Concurrently fetch traditional equity quote and OKX tokenized quote
        eq_task = self.equity_provider.get_quote(sym_upper)
        token_task = self.tokenized_provider.get_tokenized_quote(f"x{sym_upper}")

        eq_res, token_res = await asyncio.gather(eq_task, token_task, return_exceptions=True)

        eq_quote: Optional[NormalizedEquityQuote] = eq_res if isinstance(eq_res, NormalizedEquityQuote) else None
        token_quote: Optional[NormalizedTokenizedEquityQuote] = token_res if isinstance(token_res, NormalizedTokenizedEquityQuote) else None

        has_tokenized = token_quote is not None and token_quote.data_status != "unavailable"
        comparison_available = False
        unavailability_reason = None
        diff_abs = None
        diff_pct = None

        if not eq_quote or eq_quote.data_status == "provider_not_configured":
            unavailability_reason = "Traditional equity provider (Finnhub) not configured"
        elif eq_quote.data_status == "unavailable" or not eq_quote.price:
            unavailability_reason = "Traditional equity market data currently unavailable"
        elif not token_quote or token_quote.data_status == "unavailable" or not token_quote.price:
            unavailability_reason = "OKX tokenized equity feed currently unavailable"
        else:
            try:
                eq_px = Decimal(eq_quote.price)
                tok_px = Decimal(token_quote.price)
                delta = tok_px - eq_px
                diff_abs = f"{delta:+.2f}"
                if eq_px > 0:
                    pct = float((delta / eq_px) * Decimal("100"))
                    diff_pct = round(pct, 2)
                comparison_available = True
            except Exception as e:
                logger.warning(f"Error calculating comparison difference for {sym_upper}: {e}")
                unavailability_reason = "Calculation error"

        response = EquityComparisonResponse(
            underlying_symbol=sym_upper,
            underlying_name=comp_name,
            comparison_available=comparison_available,
            unavailability_reason=unavailability_reason,
            underlying_price=eq_quote.price if (eq_quote and eq_quote.price) else None,
            underlying_provider=eq_quote.provider if eq_quote else self.equity_provider.provider_name,
            underlying_data_status=eq_quote.data_status if eq_quote else "provider_not_configured",
            underlying_market_state=eq_quote.market_state if eq_quote else "closed",
            underlying_timestamp=eq_quote.market_timestamp if eq_quote else None,
            tokenized_counterpart_available=has_tokenized,
            tokenized_symbol=token_quote.symbol if token_quote else None,
            tokenized_provider=token_quote.provider if token_quote else None,
            tokenized_data_status=token_quote.data_status if token_quote else "unavailable",
            tokenized_price=token_quote.price if (token_quote and token_quote.price) else None,
            tokenized_timestamp=token_quote.timestamp if token_quote else None,
            price_difference_abs=diff_abs,
            price_difference_pct=diff_pct,
            comparison_label="Reference Price Difference",
            disclaimer="Prices may differ due to market hours, liquidity, venue structure, and update timing. Not an arbitrage signal."
        )

        await self.cache.set(cache_key, response, ttl=20.0)
        return response
