import httpx
import os
import logging
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

from app.modules.market_data.equity_base import BaseEquityMarketDataProvider
from app.modules.market_data.schemas import (
    NormalizedEquityQuote,
    AssetInfo,
    NormalizedCandle,
    AssetCategory,
)
from app.modules.market_data.exceptions import InvalidAssetError, ProviderUnavailableError
from app.modules.market_data.cache import global_cache

logger = logging.getLogger(__name__)

# Supported top 10 US Equities watch universe with company names
SUPPORTED_EQUITIES_MAP: Dict[str, str] = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "NVDA": "NVIDIA Corporation",
    "META": "Meta Platforms Inc.",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla Inc.",
    "MSTR": "MicroStrategy Inc.",
    "MU": "Micron Technology Inc.",
    "MRVL": "Marvell Technology Inc.",
}

class FinnhubEquityProvider(BaseEquityMarketDataProvider):
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        timeout: float = 6.0,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("FINNHUB_API_KEY", "").strip()
        self._custom_client = http_client
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "Finnhub"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 4)

    def is_us_market_open(self) -> bool:
        """Determine if US stock exchanges (NYSE/NASDAQ) are open (Monday-Friday 13:30-20:00 UTC)"""
        now_utc = datetime.now(timezone.utc)
        # Weekday: Monday is 0 and Sunday is 6
        if now_utc.weekday() >= 5:
            return False
        
        market_open_min = 13 * 60 + 30 # 13:30 UTC
        market_close_min = 20 * 60     # 20:00 UTC
        curr_min = now_utc.hour * 60 + now_utc.minute

        return market_open_min <= curr_min < market_close_min

    async def _get_client(self) -> httpx.AsyncClient:
        if self._custom_client:
            return self._custom_client
        return httpx.AsyncClient(timeout=self._timeout)

    async def get_supported_equities(self) -> List[AssetInfo]:
        assets: List[AssetInfo] = []
        is_open = self.is_us_market_open()
        market_status = "open" if is_open else "closed"

        for sym, name in SUPPORTED_EQUITIES_MAP.items():
            assets.append(
                AssetInfo(
                    internal_id=f"equity:{sym.lower()}",
                    symbol=sym,
                    display_symbol=sym,
                    name=name,
                    category=AssetCategory.EQUITY.value,
                    provider=self.provider_name,
                    provider_symbol=sym,
                    quote_currency="USD",
                    venue="NASDAQ",
                    market_status=market_status,
                    tradable_on_provider=False,
                    metadata={"provider_configured": self.is_configured}
                )
            )
        return assets

    async def get_quote(self, symbol: str) -> NormalizedEquityQuote:
        sym_upper = symbol.upper()
        if sym_upper not in SUPPORTED_EQUITIES_MAP:
            raise InvalidAssetError(symbol)

        comp_name = SUPPORTED_EQUITIES_MAP[sym_upper]
        is_open = self.is_us_market_open()
        market_state = "open" if is_open else "closed"

        # If Finnhub is not configured, return clear provider_not_configured status with zero fake prices
        if not self.is_configured:
            return NormalizedEquityQuote(
                symbol=sym_upper,
                name=comp_name,
                asset_type=AssetCategory.EQUITY.value,
                provider=self.provider_name,
                price=None,
                previous_close=None,
                open_price=None,
                high=None,
                low=None,
                change_abs=None,
                change_pct=None,
                volume=None,
                currency="USD",
                market_timestamp=None,
                retrieved_at=datetime.now(timezone.utc),
                market_state=market_state,
                data_status="provider_not_configured"
            )

        # Live Finnhub fetch
        url = f"{self.BASE_URL}/quote?symbol={sym_upper}&token={self.api_key}"
        try:
            client = await self._get_client()
            should_close = self._custom_client is None
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
            finally:
                if should_close:
                    await client.aclose()

            c = data.get("c", 0) # Current price
            d = data.get("d", 0) # Change
            dp = data.get("dp", 0) # Percent change
            h = data.get("h", 0) # High
            l = data.get("l", 0) # Low
            o = data.get("o", 0) # Open
            pc = data.get("pc", 0) # Prev close
            t = data.get("t", 0) # Timestamp

            if c == 0 and pc == 0:
                raise ProviderUnavailableError(self.provider_name, f"Finnhub returned 0 price for {sym_upper}")

            ts_dt = datetime.fromtimestamp(t, tz=timezone.utc) if t else datetime.now(timezone.utc)

            return NormalizedEquityQuote(
                symbol=sym_upper,
                name=comp_name,
                asset_type=AssetCategory.EQUITY.value,
                provider=self.provider_name,
                price=str(c),
                previous_close=str(pc) if pc else None,
                open_price=str(o) if o else None,
                high=str(h) if h else None,
                low=str(l) if l else None,
                change_abs=f"{d:+.2f}" if d is not None else None,
                change_pct=round(float(dp), 2) if dp is not None else None,
                volume=None,
                currency="USD",
                market_timestamp=ts_dt,
                retrieved_at=datetime.now(timezone.utc),
                market_state=market_state,
                data_status="live"
            )
        except Exception as e:
            logger.warning(f"Failed to fetch live Finnhub quote for {sym_upper}: {e}")
            return NormalizedEquityQuote(
                symbol=sym_upper,
                name=comp_name,
                asset_type=AssetCategory.EQUITY.value,
                provider=self.provider_name,
                price=None,
                previous_close=None,
                open_price=None,
                high=None,
                low=None,
                change_abs=None,
                change_pct=None,
                volume=None,
                currency="USD",
                market_timestamp=None,
                retrieved_at=datetime.now(timezone.utc),
                market_state=market_state,
                data_status="unavailable"
            )

    async def get_quotes(self, symbols: List[str]) -> List[NormalizedEquityQuote]:
        tasks = [self.get_quote(s) for s in symbols if s.upper() in SUPPORTED_EQUITIES_MAP]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        quotes = []
        for r in results:
            if isinstance(r, NormalizedEquityQuote):
                quotes.append(r)
        return quotes

    async def get_candles(self, symbol: str, timeframe: str = "1H", limit: int = 100) -> List[NormalizedCandle]:
        # Live candles require Finnhub stock candle endpoints if configured
        return []
