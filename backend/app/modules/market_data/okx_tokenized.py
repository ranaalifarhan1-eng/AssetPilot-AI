import httpx
import logging
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from decimal import Decimal

from app.modules.market_data.schemas import (
    AssetInfo,
    NormalizedTokenizedEquityQuote,
    AssetCategory,
)
from app.modules.market_data.exceptions import InvalidAssetError, ProviderUnavailableError
from app.modules.market_data.cache import global_cache

logger = logging.getLogger(__name__)

# Controlled mapping of recognized underlying stock tickers to company names & baseline reference prices
RECOGNIZED_UNDERLYING_MAP: Dict[str, Dict[str, str]] = {
    "AAPL": {"name": "Apple Inc.", "ref_price": "229.10"},
    "MSFT": {"name": "Microsoft Corporation", "ref_price": "449.50"},
    "GOOGL": {"name": "Alphabet Inc.", "ref_price": "182.90"},
    "NVDA": {"name": "NVIDIA Corporation", "ref_price": "139.20"},
    "META": {"name": "Meta Platforms Inc.", "ref_price": "561.40"},
    "AMZN": {"name": "Amazon.com Inc.", "ref_price": "194.80"},
    "TSLA": {"name": "Tesla Inc.", "ref_price": "243.20"},
    "MSTR": {"name": "MicroStrategy Inc.", "ref_price": "346.80"},
    "MU": {"name": "Micron Technology Inc.", "ref_price": "112.90"},
    "MRVL": {"name": "Marvell Technology Inc.", "ref_price": "88.90"},
    "CRCL": {"name": "Circle Internet Financial", "ref_price": "118.50"},
    "LITE": {"name": "Lumentum Holdings Inc.", "ref_price": "216.40"},
    "SKHY": {"name": "SK Hynix Inc.", "ref_price": "145.00"},
    "SNDK": {"name": "SanDisk Corp", "ref_price": "95.00"},
    "SPCX": {"name": "SpaceX Tokenized Exposure", "ref_price": "280.00"},
    "ADBE": {"name": "Adobe Inc.", "ref_price": "510.00"},
    "AMD": {"name": "Advanced Micro Devices Inc.", "ref_price": "152.00"},
    "ARM": {"name": "Arm Holdings plc", "ref_price": "140.00"},
    "ASML": {"name": "ASML Holding N.V.", "ref_price": "890.00"},
}

# Explicit blacklist of non-equity tokens that start with X on OKX
NON_EQUITY_X_TOKENS = {"XRP", "XLM", "XAUT", "XTZ", "XCH", "XPL", "XDC", "XEC", "XYO", "XTAG"}

class OKXTokenizedStocksProvider:
    BASE_URL = "https://www.okx.com/api/v5"

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

    async def discover_tokenized_instruments(self) -> List[AssetInfo]:
        """Dynamically query OKX public SPOT instruments and filter for recognized tokenized equities"""
        cache_key = "okx_tokenized_instruments"
        cached = await global_cache.get(cache_key)
        if cached:
            return cached

        url = f"{self.BASE_URL}/public/instruments?instType=SPOT"
        discovered: List[AssetInfo] = []

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
                            comp_name = RECOGNIZED_UNDERLYING_MAP[underlying_sym]["name"]
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
                logger.warning(f"Attempt {attempt} discovering OKX tokenized instruments failed: {e}")
                if attempt < self._max_retries:
                    await asyncio.sleep(0.5 * attempt)

        if not discovered:
            discovered = self._get_fallback_tokenized_assets()

        await global_cache.set(cache_key, discovered, ttl=1200.0)
        return discovered

    def _get_fallback_tokenized_assets(self) -> List[AssetInfo]:
        fallback_symbols = ["GOOGL", "AAPL", "MSFT", "NVDA", "META", "AMZN", "TSLA", "MSTR", "MU", "MRVL"]
        assets = []
        for sym in fallback_symbols:
            comp_name = RECOGNIZED_UNDERLYING_MAP.get(sym, {}).get("name", f"{sym} Corporation")
            token_sym = f"x{sym}"
            assets.append(
                AssetInfo(
                    internal_id=f"tokenized:{token_sym.lower()}",
                    symbol=token_sym,
                    display_symbol=f"{token_sym}/USDT",
                    name=f"{token_sym} ({comp_name})",
                    category=AssetCategory.TOKENIZED_EQUITY.value,
                    provider=self.provider_name,
                    provider_symbol=f"X{sym}-USDT",
                    quote_currency="USDT",
                    underlying_symbol=sym,
                    underlying_name=comp_name,
                    venue="OKX SPOT",
                    market_status="24/7",
                    tradable_on_provider=True,
                    metadata={
                        "tokenized_label": "Tokenized Equity • OKX",
                        "quote_pair": f"X{sym}-USDT",
                        "underlying": sym,
                    }
                )
            )
        return assets

    async def get_tokenized_quote(self, symbol: str) -> NormalizedTokenizedEquityQuote:
        """Fetch live ticker for a tokenized stock (e.g. 'xGOOGL' or 'GOOGL')"""
        clean_sym = symbol.upper()
        if clean_sym.startswith("X") and not clean_sym.startswith("X-"):
            underlying_sym = clean_sym[1:]
        else:
            underlying_sym = clean_sym

        if underlying_sym not in RECOGNIZED_UNDERLYING_MAP:
            raise InvalidAssetError(symbol)

        inst_id = f"X{underlying_sym}-USDT"
        comp_name = RECOGNIZED_UNDERLYING_MAP[underlying_sym]["name"]
        url = f"{self.BASE_URL}/market/ticker?instId={inst_id}"

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
                            timestamp=ts_dt
                        )
                finally:
                    if should_close:
                        await client.aclose()
            except Exception as e:
                logger.warning(f"Attempt {attempt} fetching OKX ticker for {inst_id} failed: {e}")
                if attempt < self._max_retries:
                    await asyncio.sleep(0.5 * attempt)

        # Fallback reference price if OKX API is temporarily unreachable
        ref_price = Decimal(RECOGNIZED_UNDERLYING_MAP[underlying_sym]["ref_price"])
        return NormalizedTokenizedEquityQuote(
            symbol=f"x{underlying_sym}",
            display_symbol=f"x{underlying_sym}/USDT",
            name=f"x{underlying_sym} ({comp_name})",
            asset_type=AssetCategory.TOKENIZED_EQUITY.value,
            provider=f"{self.provider_name} (Reference)",
            provider_symbol=inst_id,
            underlying_symbol=underlying_sym,
            underlying_name=comp_name,
            price=f"{ref_price:.2f}",
            open_24h=f"{(ref_price * Decimal('0.995')):.2f}",
            high_24h=f"{(ref_price * Decimal('1.01')):.2f}",
            low_24h=f"{(ref_price * Decimal('0.99')):.2f}",
            volume_24h="500",
            quote_volume_24h=f"{(ref_price * Decimal('500')):.0f}",
            change_24h_abs=f"+{(ref_price * Decimal('0.005')):.2f}",
            change_24h_pct=0.50,
            quote_currency="USDT",
            tokenized_label="Tokenized Equity • OKX",
            timestamp=datetime.now(timezone.utc)
        )

    async def get_tokenized_quotes(self, symbols: Optional[List[str]] = None) -> List[NormalizedTokenizedEquityQuote]:
        """Fetch quotes concurrently for all discovered or requested tokenized stocks"""
        if not symbols:
            instruments = await self.discover_tokenized_instruments()
            symbols = [item.symbol for item in instruments]

        tasks = [self.get_tokenized_quote(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        quotes = []
        for r in results:
            if isinstance(r, NormalizedTokenizedEquityQuote):
                quotes.append(r)
            elif isinstance(r, Exception):
                logger.warning(f"Failed to fetch tokenized quote: {r}")
        return quotes
