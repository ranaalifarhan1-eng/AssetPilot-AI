import httpx
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.modules.market_data.base import BaseMarketDataProvider
from app.modules.market_data.schemas import NormalizedTicker, NormalizedCandle, AssetInfo
from app.modules.market_data.exceptions import (
    InvalidAssetError,
    InvalidTimeframeError,
    ProviderUnavailableError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)

SUPPORTED_ASSETS_MAP: Dict[str, AssetInfo] = {
    "BTC": AssetInfo(
        symbol="BTC",
        name="Bitcoin",
        category="Crypto",
        provider_symbol="BTC-USDT"
    ),
    "ETH": AssetInfo(
        symbol="ETH",
        name="Ethereum",
        category="Crypto",
        provider_symbol="ETH-USDT"
    ),
    "SOL": AssetInfo(
        symbol="SOL",
        name="Solana",
        category="Crypto",
        provider_symbol="SOL-USDT"
    ),
}

TIMEFRAME_MAP: Dict[str, str] = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1H": "1H",
    "4H": "4H",
    "1D": "1D",
}

class OKXMarketDataProvider(BaseMarketDataProvider):
    BASE_URL = "https://www.okx.com/api/v5/market"

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None, timeout: float = 6.0, max_retries: int = 2):
        self._custom_client = http_client
        self._timeout = timeout
        self._max_retries = max_retries

    @property
    def provider_name(self) -> str:
        return "OKX"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._custom_client:
            return self._custom_client
        return httpx.AsyncClient(timeout=self._timeout)

    async def get_supported_assets(self) -> List[AssetInfo]:
        return list(SUPPORTED_ASSETS_MAP.values())

    async def get_ticker(self, symbol: str) -> NormalizedTicker:
        symbol_upper = symbol.upper()
        if symbol_upper not in SUPPORTED_ASSETS_MAP:
            raise InvalidAssetError(symbol)

        asset_info = SUPPORTED_ASSETS_MAP[symbol_upper]
        inst_id = asset_info.provider_symbol
        url = f"{self.BASE_URL}/ticker?instId={inst_id}"

        data = await self._fetch_okx_json(url)
        try:
            raw_list = data.get("data", [])
            if not raw_list:
                raise ProviderUnavailableError(self.provider_name, f"Empty response for ticker {symbol}")
            raw = raw_list[0]
            return self._normalize_ticker(asset_info, raw)
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing OKX ticker response for {symbol}: {e}")
            raise ProviderUnavailableError(self.provider_name, f"Failed to parse ticker data for {symbol}")

    async def get_tickers(self, symbols: List[str]) -> List[NormalizedTicker]:
        """Fetch tickers concurrently for all symbols"""
        tasks = [self.get_ticker(s) for s in symbols if s.upper() in SUPPORTED_ASSETS_MAP]
        if not tasks:
            return []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        tickers: List[NormalizedTicker] = []
        for res in results:
            if isinstance(res, NormalizedTicker):
                tickers.append(res)
            elif isinstance(res, Exception):
                logger.warning(f"Error fetching ticker in get_tickers: {res}")
        return tickers

    async def get_candles(self, symbol: str, timeframe: str = "1H", limit: int = 100) -> List[NormalizedCandle]:
        symbol_upper = symbol.upper()
        if symbol_upper not in SUPPORTED_ASSETS_MAP:
            raise InvalidAssetError(symbol)

        if timeframe not in TIMEFRAME_MAP:
            raise InvalidTimeframeError(timeframe)

        if limit < 1 or limit > 300:
            limit = min(max(1, limit), 300)

        inst_id = SUPPORTED_ASSETS_MAP[symbol_upper].provider_symbol
        okx_bar = TIMEFRAME_MAP[timeframe]
        url = f"{self.BASE_URL}/candles?instId={inst_id}&bar={okx_bar}&limit={limit}"

        data = await self._fetch_okx_json(url)
        try:
            raw_candles = data.get("data", [])
            normalized: List[NormalizedCandle] = []
            for item in raw_candles:
                ts_ms = int(item[0])
                ts_dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
                candle = NormalizedCandle(
                    timestamp=ts_dt,
                    open=str(item[1]),
                    high=str(item[2]),
                    low=str(item[3]),
                    close=str(item[4]),
                    volume=str(item[5])
                )
                normalized.append(candle)
            
            normalized.reverse()
            return normalized
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing OKX candles for {symbol}: {e}")
            raise ProviderUnavailableError(self.provider_name, f"Failed to parse candle data for {symbol}")

    async def _fetch_okx_json(self, url: str) -> Dict:
        last_exception = None
        for attempt in range(1, self._max_retries + 1):
            client = await self._get_client()
            should_close = self._custom_client is None
            try:
                response = await client.get(url)
                response.raise_for_status()
                res_json = response.json()
                if res_json.get("code") != "0":
                    msg = res_json.get("msg", "OKX API error")
                    raise ProviderUnavailableError(self.provider_name, f"OKX API error code {res_json.get('code')}: {msg}")
                return res_json
            except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as e:
                last_exception = e
                logger.warning(f"OKX fetch attempt {attempt}/{self._max_retries} failed for {url}: {e}")
                if attempt < self._max_retries:
                    await asyncio.sleep(0.5 * attempt)
            finally:
                if should_close:
                    await client.aclose()

        if isinstance(last_exception, httpx.TimeoutException):
            raise ProviderTimeoutError(self.provider_name)
        raise ProviderUnavailableError(self.provider_name, f"Network error after {self._max_retries} attempts: {str(last_exception)}")

    def _normalize_ticker(self, asset_info: AssetInfo, raw: Dict) -> NormalizedTicker:
        last_price = raw.get("last", "0")
        open_24h = raw.get("open24h", "0")
        high_24h = raw.get("high24h", "0")
        low_24h = raw.get("low24h", "0")
        vol_24h = raw.get("vol24h", "0")
        vol_ccy_24h = raw.get("volCcy24h", "0")

        last_flt = float(last_price)
        open_flt = float(open_24h)
        
        change_abs = last_flt - open_flt
        change_pct = (change_abs / open_flt * 100.0) if open_flt > 0 else 0.0

        ts_ms = int(raw.get("ts", datetime.now(timezone.utc).timestamp() * 1000))
        ts_dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)

        return NormalizedTicker(
            symbol=asset_info.symbol,
            provider_symbol=asset_info.provider_symbol,
            name=asset_info.name,
            price=str(last_price),
            open_24h=str(open_24h),
            high_24h=str(high_24h),
            low_24h=str(low_24h),
            volume_24h=str(vol_24h),
            quote_volume_24h=str(vol_ccy_24h),
            change_24h_abs=f"{change_abs:+.4f}",
            change_24h_pct=round(change_pct, 2),
            timestamp=ts_dt,
            provider=self.provider_name
        )
