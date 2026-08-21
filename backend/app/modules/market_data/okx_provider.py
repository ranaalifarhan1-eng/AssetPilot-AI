import httpx
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.modules.market_data.base import BaseMarketDataProvider
from app.modules.market_data.schemas import NormalizedTicker, NormalizedCandle, AssetInfo, AssetCategory
from app.modules.market_data.exceptions import (
    InvalidAssetError,
    InvalidTimeframeError,
    ProviderUnavailableError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)

SUPPORTED_ASSETS_MAP: Dict[str, AssetInfo] = {
    "BTC": AssetInfo(
        internal_id="crypto:btc",
        symbol="BTC",
        display_symbol="BTC/USDT",
        name="Bitcoin",
        category=AssetCategory.CRYPTO.value,
        provider="OKX",
        provider_symbol="BTC-USDT",
        quote_currency="USDT",
        venue="OKX SPOT",
        market_status="24/7",
        tradable_on_provider=True
    ),
    "ETH": AssetInfo(
        internal_id="crypto:eth",
        symbol="ETH",
        display_symbol="ETH/USDT",
        name="Ethereum",
        category=AssetCategory.CRYPTO.value,
        provider="OKX",
        provider_symbol="ETH-USDT",
        quote_currency="USDT",
        venue="OKX SPOT",
        market_status="24/7",
        tradable_on_provider=True
    ),
    "SOL": AssetInfo(
        internal_id="crypto:sol",
        symbol="SOL",
        display_symbol="SOL/USDT",
        name="Solana",
        category=AssetCategory.CRYPTO.value,
        provider="OKX",
        provider_symbol="SOL-USDT",
        quote_currency="USDT",
        venue="OKX SPOT",
        market_status="24/7",
        tradable_on_provider=True
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
    BASE_URL = "https://www.okx.cab/api/v5/market"
    FALLBACK_URL = "https://www.okx.com/api/v5/market"

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None, timeout: float = 6.0, max_retries: int = 2):
        self._custom_client = http_client
        self._timeout = timeout
        self._max_retries = max_retries
        self._default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

    @property
    def provider_name(self) -> str:
        return "OKX"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._custom_client:
            return self._custom_client
        return httpx.AsyncClient(timeout=self._timeout, headers=self._default_headers)

    async def get_supported_assets(self) -> List[AssetInfo]:
        return list(SUPPORTED_ASSETS_MAP.values())

    async def get_ticker(self, symbol: str) -> NormalizedTicker:
        symbol_upper = symbol.upper()
        
        if symbol_upper in SUPPORTED_ASSETS_MAP:
            asset_info = SUPPORTED_ASSETS_MAP[symbol_upper]
            inst_id = asset_info.provider_symbol
        else:
            inst_id = f"{symbol_upper}-USDT"
            asset_info = AssetInfo(
                internal_id=f"crypto:{symbol_upper.lower()}",
                symbol=symbol_upper,
                display_symbol=f"{symbol_upper}/USDT",
                name=symbol_upper,
                category=AssetCategory.CRYPTO.value,
                provider=self.provider_name,
                provider_symbol=inst_id,
                quote_currency="USDT",
                venue="OKX SPOT",
                market_status="24/7",
                tradable_on_provider=True
            )

        url = f"{self.BASE_URL}/ticker?instId={inst_id}"

        try:
            data = await self._fetch_okx_json(url)
            raw_list = data.get("data", [])
            if not raw_list:
                raise InvalidAssetError(symbol)
            raw = raw_list[0]
            return self._normalize_ticker(asset_info, raw)
        except InvalidAssetError:
            raise
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing OKX ticker response for {symbol}: {e}")
            raise ProviderUnavailableError(self.provider_name, f"Failed to parse ticker data for {symbol}")

    async def get_tickers(self, symbols: List[str]) -> List[NormalizedTicker]:
        """Fetch supported overview tickers with one OKX bulk request."""
        wanted = {s.upper() for s in symbols if s.upper() in SUPPORTED_ASSETS_MAP}
        if not wanted:
            return []
        data = await self._fetch_okx_json(f"{self.BASE_URL}/tickers?instType=SPOT")
        rows = {row.get("instId"): row for row in data.get("data", [])}
        return [
            self._normalize_ticker(SUPPORTED_ASSETS_MAP[sym], rows[SUPPORTED_ASSETS_MAP[sym].provider_symbol])
            for sym in wanted if SUPPORTED_ASSETS_MAP[sym].provider_symbol in rows
        ]

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
            return [self._normalize_candle(item) for item in raw_candles]
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing OKX candle response for {symbol}: {e}")
            raise ProviderUnavailableError(self.provider_name, f"Failed to parse candle data for {symbol}")

    async def _fetch_okx_json(self, url: str) -> Dict:
        """Fetch JSON from primary URL with fallback and retries."""
        endpoints = [url]
        if self.BASE_URL in url:
            endpoints.append(url.replace(self.BASE_URL, self.FALLBACK_URL))

        last_exception = None
        for endpoint_url in endpoints:
            for attempt in range(1, self._max_retries + 1):
                try:
                    client = await self._get_client()
                    should_close = self._custom_client is None
                    try:
                        resp = await client.get(endpoint_url)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("code") == "0":
                                return data
                            else:
                                msg = data.get("msg", "Unknown OKX API error")
                                logger.warning(f"OKX API error: code {data.get('code')} - {msg}")
                                if data.get("code") in ["51000", "51001"]:
                                    raise InvalidAssetError(endpoint_url)
                                raise ProviderUnavailableError(self.provider_name, f"Code {data.get('code')}: {msg}")
                        elif resp.status_code in [400, 404]:
                            raise InvalidAssetError(endpoint_url)
                        else:
                            raise ProviderUnavailableError(self.provider_name, f"HTTP {resp.status_code}")
                    finally:
                        if should_close:
                            await client.aclose()
                except (InvalidAssetError, InvalidTimeframeError):
                    raise
                except httpx.TimeoutException as e:
                    last_exception = ProviderTimeoutError(self.provider_name, f"Timeout after {self._timeout}s (attempt {attempt})")
                    if attempt < self._max_retries:
                        await asyncio.sleep(0.2 * attempt)
                except httpx.RequestError as e:
                    last_exception = ProviderUnavailableError(self.provider_name, f"Network error: {str(e)}")
                    if attempt < self._max_retries:
                        await asyncio.sleep(0.2 * attempt)
                except Exception as e:
                    last_exception = e
                    break

        if isinstance(last_exception, (InvalidAssetError, InvalidTimeframeError, ProviderUnavailableError, ProviderTimeoutError)):
            raise last_exception
        raise ProviderUnavailableError(self.provider_name, str(last_exception) if last_exception else "Unknown error")

    def _normalize_ticker(self, asset_info: AssetInfo, raw: Dict) -> NormalizedTicker:
        price = str(raw.get("last", "0"))
        open_24h = str(raw.get("open24h", "0"))
        high_24h = str(raw.get("high24h", "0"))
        low_24h = str(raw.get("low24h", "0"))
        vol_24h = str(raw.get("vol24h", "0"))
        vol_ccy_24h = str(raw.get("volCcy24h", "0"))

        try:
            last_f = float(price)
            open_f = float(open_24h)
            chg_abs_f = last_f - open_f
            chg_pct_f = ((last_f - open_f) / open_f * 100.0) if open_f != 0 else 0.0
            chg_abs = f"{chg_abs_f:.4f}"
            chg_pct = round(chg_pct_f, 2)
        except (ValueError, ZeroDivisionError):
            chg_abs = "0.00"
            chg_pct = 0.0

        ts_raw = raw.get("ts")
        if ts_raw:
            try:
                dt = datetime.fromtimestamp(int(ts_raw) / 1000.0, tz=timezone.utc)
                iso_ts = dt.isoformat()
            except Exception:
                iso_ts = datetime.now(timezone.utc).isoformat()
        else:
            iso_ts = datetime.now(timezone.utc).isoformat()

        return NormalizedTicker(
            symbol=asset_info.symbol,
            provider_symbol=asset_info.provider_symbol,
            name=asset_info.name,
            price=price,
            open_24h=open_24h,
            high_24h=high_24h,
            low_24h=low_24h,
            volume_24h=vol_24h,
            quote_volume_24h=vol_ccy_24h,
            change_24h_abs=chg_abs,
            change_24h_pct=chg_pct,
            timestamp=iso_ts,
            provider=self.provider_name,
            data_status="live"
        )

    def _normalize_candle(self, raw: List) -> NormalizedCandle:
        ts_ms = int(raw[0])
        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
        return NormalizedCandle(
            timestamp=dt.isoformat(),
            open=str(raw[1]),
            high=str(raw[2]),
            low=str(raw[3]),
            close=str(raw[4]),
            volume=str(raw[5])
        )
