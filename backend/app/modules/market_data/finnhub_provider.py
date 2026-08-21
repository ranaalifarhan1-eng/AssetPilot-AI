import httpx
import os
import logging
import asyncio
from typing import List, Dict, Optional, Any
from datetime import date, datetime, time, timedelta, timezone
import calendar
from zoneinfo import ZoneInfo
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

    def get_us_market_state(self, at: Optional[datetime] = None) -> str:
        """Deterministic regular-session state using New York time and major full-day holidays."""
        instant = at or datetime.now(timezone.utc)
        if instant.tzinfo is None:
            return "unknown"
        eastern = instant.astimezone(ZoneInfo("America/New_York"))
        if eastern.weekday() >= 5 or eastern.date() in self._market_holidays(eastern.year):
            return "closed"
        return "open" if time(9, 30) <= eastern.time().replace(tzinfo=None) < time(16, 0) else "closed"

    def is_us_market_open(self) -> bool:
        return self.get_us_market_state() == "open"

    @staticmethod
    def _market_holidays(year: int) -> set[date]:
        def observed(day: date) -> date:
            if day.weekday() == 5:
                return day - timedelta(days=1)
            if day.weekday() == 6:
                return day + timedelta(days=1)
            return day
        def nth_weekday(month: int, weekday: int, n: int) -> date:
            first = date(year, month, 1)
            return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))
        def last_weekday(month: int, weekday: int) -> date:
            last = date(year, month, calendar.monthrange(year, month)[1])
            return last - timedelta(days=(last.weekday() - weekday) % 7)
        # Anonymous Gregorian computus; NYSE Good Friday is two days before Easter.
        a, b, c = year % 19, year // 100, year % 100
        d, e = b // 4, b % 4
        f, g = (b + 8) // 25, (b - (b + 8) // 25 + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i, k = c // 4, c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        easter_month = (h + l - 7 * m + 114) // 31
        easter_day = (h + l - 7 * m + 114) % 31 + 1
        good_friday = date(year, easter_month, easter_day) - timedelta(days=2)
        return {
            observed(date(year, 1, 1)), nth_weekday(1, 0, 3), nth_weekday(2, 0, 3),
            good_friday, last_weekday(5, 0), observed(date(year, 6, 19)),
            observed(date(year, 7, 4)), nth_weekday(9, 0, 1), nth_weekday(11, 3, 4),
            observed(date(year, 12, 25)),
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._custom_client:
            return self._custom_client
        return httpx.AsyncClient(timeout=self._timeout)

    async def get_supported_equities(self) -> List[AssetInfo]:
        assets: List[AssetInfo] = []
        market_status = self.get_us_market_state()

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
        market_state = self.get_us_market_state()

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
                for attempt in range(2):
                    resp = await client.get(url)
                    if resp.status_code != 429:
                        resp.raise_for_status()
                        data = resp.json()
                        break
                    retry_after = resp.headers.get("Retry-After", "0")
                    try:
                        delay = max(0.0, min(float(retry_after), 2.0))
                    except ValueError:
                        delay = 0.0
                    if attempt == 0 and delay > 0:
                        await asyncio.sleep(delay)
                        continue
                    raise ProviderUnavailableError(self.provider_name, "Rate limited by Finnhub")
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
        valid_symbols = [s for s in symbols if s.upper() in SUPPORTED_EQUITIES_MAP]
        if self._custom_client:
            results = await asyncio.gather(*(self.get_quote(s) for s in valid_symbols), return_exceptions=True)
        else:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                pooled = FinnhubEquityProvider(api_key=self.api_key, http_client=client, timeout=self._timeout)
                results = await asyncio.gather(*(pooled.get_quote(s) for s in valid_symbols), return_exceptions=True)
        quotes = []
        for r in results:
            if isinstance(r, NormalizedEquityQuote):
                quotes.append(r)
        return quotes

    async def get_candles(self, symbol: str, timeframe: str = "1H", limit: int = 100) -> List[NormalizedCandle]:
        # Live candles require Finnhub stock candle endpoints if configured
        return []
