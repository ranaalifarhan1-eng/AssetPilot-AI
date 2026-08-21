import httpx
import logging
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from app.modules.market_data.schemas import (
    AssetInfo,
    NormalizedTokenizedEquityQuote,
    AssetCategory,
)
from app.modules.market_data.exceptions import InvalidAssetError, ProviderUnavailableError
from app.modules.market_data.cache import global_cache

logger = logging.getLogger(__name__)

# Controlled mapping of recognized underlying stock tickers to company names
RECOGNIZED_UNDERLYING_MAP: Dict[str, str] = {
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
    "CRCL": "Circle Internet Financial",
    "LITE": "Lumentum Holdings Inc.",
    "SKHY": "SK Hynix Inc.",
    "SNDK": "SanDisk Corp",
    "SPCX": "SpaceX Tokenized Exposure",
    "ADBE": "Adobe Inc.",
    "AMD": "Advanced Micro Devices Inc.",
    "ARM": "Arm Holdings plc",
    "ASML": "ASML Holding N.V.",
}

# Explicit blacklist of non-equity tokens that start with X on OKX
NON_EQUITY_X_TOKENS = {"XRP", "XLM", "XAUT", "XTZ", "XCH", "XPL", "XDC", "XEC", "XYO", "XTAG"}

class OKXTokenizedStocksProvider:
    BASE_URLS = [
        "https://www.okx.cab/api/v5",
        "https://www.okx.com/api/v5",
    ]

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

    async def discover_tokenized_instruments(self) -> List[AssetInfo]:
        """Dynamically query OKX public SPOT instruments and filter for recognized tokenized equities"""
        cache_key = "okx_tokenized_instruments"
        cached = await global_cache.get(cache_key)
        if cached:
            return cached

        discovered: List[AssetInfo] = []

        for base_url in self.BASE_URLS:
            url = f"{base_url}/public/instruments?instType=SPOT"
            for attempt in range(1, self._max_retries + 1):
                try:
                    client = await self._get_client()
                    should_close = self._custom_client is None
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        data = resp.json().get("data", [])
                    finally:
                        if should_close:
                            await client.aclose()

                    for item in data:
                        inst_id = item.get("instId", "")
                        if inst_id.startswith("X") and inst_id.endswith("-USDT"):
                            raw_base = inst_id.split("-")[0]
                            token_sym = f"x{raw_base[1:]}"
                            underlying_sym = raw_base[1:]

                            if underlying_sym in NON_EQUITY_X_TOKENS:
                                continue

                            if underlying_sym in RECOGNIZED_UNDERLYING_MAP:
                                comp_name = RECOGNIZED_UNDERLYING_MAP[underlying_sym]
                                discovered.append(
                                    AssetInfo(
                                        internal_id=f"tokenized:{token_sym.lower()}",
                                        symbol=token_sym,
                                        display_symbol=f"{token_sym}/USDT",
                                        name=f"{token_sym} ({comp_name})",
                                        category=AssetCategory.TOKENIZED_EQUITY.value,
                                        provider=self.provider_name,
                                        provider_symbol=inst_id,
                                        quote_currency="USDT",
                                        underlying_symbol=underlying_sym,
                                        underlying_name=comp_name,
                                        venue="OKX SPOT",
                                        market_status="24/7",
                                        tradable_on_provider=True,
                                        metadata={
                                            "tokenized_label": "Tokenized Equity • OKX",
                                            "quote_pair": inst_id,
                                            "underlying": underlying_sym,
                                        }
                                    )
                                )
                    if discovered:
                        break
                except Exception as e:
                    logger.debug(f"Attempt {attempt} discovering OKX tokenized instruments from {base_url} failed: {e}")
                    if attempt < self._max_retries:
                        await asyncio.sleep(0.3 * attempt)
            if discovered:
                break

        # Cache for 20 minutes
        if discovered:
            await global_cache.set(cache_key, discovered, ttl=1200.0)

        return discovered

    async def get_tokenized_quote(self, symbol: str) -> NormalizedTokenizedEquityQuote:
        """Fetch live ticker for a tokenized stock from OKX SPOT public API"""
        clean_sym = symbol.upper()
        if clean_sym.startswith("X") and not clean_sym.startswith("X-"):
            underlying_sym = clean_sym[1:]
        else:
            underlying_sym = clean_sym

        if underlying_sym not in RECOGNIZED_UNDERLYING_MAP:
            raise InvalidAssetError(symbol)

        inst_id = f"X{underlying_sym}-USDT"
        comp_name = RECOGNIZED_UNDERLYING_MAP[underlying_sym]

        for base_url in self.BASE_URLS:
            url = f"{base_url}/market/ticker?instId={inst_id}"
            for attempt in range(1, self._max_retries + 1):
                try:
                    client = await self._get_client()
                    should_close = self._custom_client is None
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        res_json = resp.json()
                        raw_list = res_json.get("data", [])
                        if raw_list:
                            raw = raw_list[0]
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

                            return NormalizedTokenizedEquityQuote(
                                symbol=f"x{underlying_sym}",
                                display_symbol=f"x{underlying_sym}/USDT",
                                name=f"x{underlying_sym} ({comp_name})",
                                asset_type=AssetCategory.TOKENIZED_EQUITY.value,
                                provider=self.provider_name,
                                provider_symbol=inst_id,
                                underlying_symbol=underlying_sym,
                                underlying_name=comp_name,
                                price=str(last_price),
                                open_24h=str(open_24h),
                                high_24h=str(high_24h),
                                low_24h=str(low_24h),
                                volume_24h=str(vol_24h),
                                quote_volume_24h=str(vol_ccy_24h),
                                change_24h_abs=f"{change_abs:+.2f}",
                                change_24h_pct=round(change_pct, 2),
                                quote_currency="USDT",
                                tokenized_label="Tokenized Equity • OKX",
                                timestamp=ts_dt,
                                retrieved_at=datetime.now(timezone.utc),
                                data_status="live"
                            )
                    finally:
                        if should_close:
                            await client.aclose()
                except Exception as e:
                    logger.debug(f"Attempt {attempt} fetching OKX ticker for {inst_id} from {base_url} failed: {e}")
                    if attempt < self._max_retries:
                        await asyncio.sleep(0.3 * attempt)

        # Return unavailable status when provider cannot be reached (zero synthetic fallback prices)
        return NormalizedTokenizedEquityQuote(
            symbol=f"x{underlying_sym}",
            display_symbol=f"x{underlying_sym}/USDT",
            name=f"x{underlying_sym} ({comp_name})",
            asset_type=AssetCategory.TOKENIZED_EQUITY.value,
            provider=self.provider_name,
            provider_symbol=inst_id,
            underlying_symbol=underlying_sym,
            underlying_name=comp_name,
            price=None,
            open_24h=None,
            high_24h=None,
            low_24h=None,
            volume_24h=None,
            quote_volume_24h=None,
            change_24h_abs=None,
            change_24h_pct=None,
            quote_currency="USDT",
            tokenized_label="Tokenized Equity • OKX",
            timestamp=None,
            retrieved_at=datetime.now(timezone.utc),
            data_status="unavailable"
        )

    async def get_tokenized_quotes(self, symbols: Optional[List[str]] = None) -> List[NormalizedTokenizedEquityQuote]:
        """Fetch discovered xStock quotes in one OKX bulk-ticker request."""
        if not symbols:
            instruments = await self.discover_tokenized_instruments()
            symbols = [item.symbol for item in instruments]
        wanted = {s.upper().removeprefix("X") for s in symbols}

        for base_url in self.BASE_URLS:
            url = f"{base_url}/market/tickers?instType=SPOT"
            for attempt in range(1, self._max_retries + 1):
                client = await self._get_client()
                should_close = self._custom_client is None
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    rows = resp.json().get("data", [])
                    quotes = []
                    for raw in rows:
                        inst_id = raw.get("instId", "")
                        if not (inst_id.startswith("X") and inst_id.endswith("-USDT")):
                            continue
                        underlying = inst_id.split("-", 1)[0][1:]
                        if underlying not in wanted or underlying not in RECOGNIZED_UNDERLYING_MAP:
                            continue
                        quotes.append(self._normalize_quote(underlying, inst_id, raw))
                    return quotes
                except Exception as e:
                    logger.debug(f"Attempt {attempt} fetching OKX bulk tickers from {base_url} failed: {e}")
                    if attempt < self._max_retries:
                        await asyncio.sleep(0.3 * attempt)
                finally:
                    if should_close:
                        await client.aclose()

        # Preserve per-symbol unavailable semantics after a bulk-provider failure.
        return [await self.get_tokenized_quote(s) for s in symbols]

    def _normalize_quote(self, underlying_sym: str, inst_id: str, raw: Dict[str, Any]) -> NormalizedTokenizedEquityQuote:
        comp_name = RECOGNIZED_UNDERLYING_MAP[underlying_sym]
        last_price = raw.get("last", "0")
        open_24h = raw.get("open24h", "0")
        last_flt = float(last_price)
        open_flt = float(open_24h)
        change_abs = last_flt - open_flt
        change_pct = (change_abs / open_flt * 100.0) if open_flt > 0 else 0.0
        ts_ms = int(raw.get("ts", datetime.now(timezone.utc).timestamp() * 1000))
        return NormalizedTokenizedEquityQuote(
            symbol=f"x{underlying_sym}", display_symbol=f"x{underlying_sym}/USDT",
            name=f"x{underlying_sym} ({comp_name})", provider_symbol=inst_id,
            underlying_symbol=underlying_sym, underlying_name=comp_name,
            price=str(last_price), open_24h=str(open_24h), high_24h=str(raw.get("high24h", "0")),
            low_24h=str(raw.get("low24h", "0")), volume_24h=str(raw.get("vol24h", "0")),
            quote_volume_24h=str(raw.get("volCcy24h", "0")), change_24h_abs=f"{change_abs:+.2f}",
            change_24h_pct=round(change_pct, 2), timestamp=datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc),
            data_status="live"
        )
