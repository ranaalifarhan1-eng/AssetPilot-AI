import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime, timezone

from app.main import app
from app.modules.market_data.schemas import (
    AssetCategory,
    AssetInfo,
    NormalizedEquityQuote,
    NormalizedTokenizedEquityQuote,
)
from app.modules.market_data.finnhub_provider import FinnhubEquityProvider, SUPPORTED_EQUITIES_MAP
from app.modules.market_data.okx_tokenized import (
    OKXTokenizedStocksProvider,
    RECOGNIZED_UNDERLYING_MAP,
    NON_EQUITY_X_TOKENS,
)
from app.modules.market_data.service import MarketDataService

client = TestClient(app)

def test_asset_taxonomy_classification():
    """Verify core asset categories and enum values"""
    assert AssetCategory.CRYPTO.value == "crypto"
    assert AssetCategory.EQUITY.value == "equity"
    assert AssetCategory.TOKENIZED_EQUITY.value == "tokenized_equity"
    assert AssetCategory.ETF.value == "etf"
    assert AssetCategory.INDEX_REFERENCE.value == "index_reference"

@pytest.mark.asyncio
async def test_finnhub_provider_unconfigured_never_fabricates_price():
    """Verify unconfigured Finnhub returns provider_not_configured with price=None (ZERO fake numbers)"""
    provider = FinnhubEquityProvider(api_key="")
    quote = await provider.get_quote("GOOGL")
    assert quote.symbol == "GOOGL"
    assert quote.name == "Alphabet Inc."
    assert quote.asset_type == "equity"
    assert quote.price is None
    assert quote.change_abs is None
    assert quote.change_pct is None
    assert quote.data_status == "provider_not_configured"

@pytest.mark.asyncio
async def test_finnhub_provider_live_quote_with_mocked_key():
    """Verify Finnhub quote parsing when key is present and provider responds"""
    provider = FinnhubEquityProvider(api_key="mock_finnhub_api_key_valid")
    mock_payload = {
        "c": 182.45,
        "d": 1.20,
        "dp": 0.66,
        "h": 183.00,
        "l": 181.10,
        "o": 181.50,
        "pc": 181.25,
        "t": 1718000000
    }

    with patch.object(provider, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_payload
        mock_resp.raise_for_status.return_value = None
        mock_client.get.return_value = mock_resp
        mock_get_client.return_value = mock_client

        quote = await provider.get_quote("GOOGL")

    assert quote.symbol == "GOOGL"
    assert quote.price == "182.45"
    assert quote.change_abs == "+1.20"
    assert quote.change_pct == 0.66
    assert quote.data_status == "live"

@pytest.mark.asyncio
async def test_okx_tokenized_instrument_filtering():
    """Verify dynamic discovery includes valid xStocks and excludes non-equity tokens"""
    mock_instruments_data = [
        {"instId": "XGOOGL-USDT", "instType": "SPOT"},
        {"instId": "XAAPL-USDT", "instType": "SPOT"},
        {"instId": "XMSTR-USDT", "instType": "SPOT"},
        {"instId": "XRP-USDT", "instType": "SPOT"},
        {"instId": "XLM-USDT", "instType": "SPOT"},
        {"instId": "BTC-USDT", "instType": "SPOT"},
    ]

    provider = OKXTokenizedStocksProvider()
    with patch.object(provider, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": "0", "data": mock_instruments_data}
        mock_resp.raise_for_status.return_value = None
        mock_client.get.return_value = mock_resp
        mock_get_client.return_value = mock_client

        with patch("app.modules.market_data.okx_tokenized.global_cache.get", return_value=None):
            discovered = await provider.discover_tokenized_instruments()

    discovered_symbols = [d.symbol for d in discovered]
    assert "xGOOGL" in discovered_symbols
    assert "xAAPL" in discovered_symbols
    assert "xMSTR" in discovered_symbols
    assert "xXRP" not in discovered_symbols
    assert "xXLM" not in discovered_symbols
    for d in discovered:
        assert d.category == "tokenized_equity"
        assert d.quote_currency == "USDT"
        assert d.underlying_symbol is not None

@pytest.mark.asyncio
async def test_okx_tokenized_quote_exact_mock():
    """Verify OKX tokenized quote preserves exact returned price and never uses hardcoded default 0.5%"""
    mock_ticker_data = [{
        "instId": "XGOOGL-USDT",
        "last": "340.28",
        "open24h": "335.00",
        "high24h": "342.00",
        "low24h": "334.50",
        "vol24h": "1250",
        "volCcy24h": "425350",
        "ts": "1718000000000"
    }]

    provider = OKXTokenizedStocksProvider()
    with patch.object(provider, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": "0", "data": mock_ticker_data}
        mock_resp.raise_for_status.return_value = None
        mock_client.get.return_value = mock_resp
        mock_get_client.return_value = mock_client

        quote = await provider.get_tokenized_quote("xGOOGL")

    assert quote.symbol == "xGOOGL"
    assert quote.price == "340.28"
    assert quote.open_24h == "335.00"
    assert quote.change_24h_pct == 1.58 # (340.28 - 335.00)/335.00 = 1.576 -> 1.58%
    assert quote.data_status == "live"

@pytest.mark.asyncio
async def test_comparison_unavailable_when_finnhub_unconfigured():
    """Verify comparison is cleanly flagged unavailable with explanation when Finnhub is not configured"""
    service = MarketDataService()

    unconfigured_equity = NormalizedEquityQuote(
        symbol="GOOGL",
        name="Alphabet Inc.",
        asset_type="equity",
        provider="Finnhub",
        price=None,
        change_abs=None,
        change_pct=None,
        currency="USD",
        market_timestamp=None,
        market_state="closed",
        data_status="provider_not_configured"
    )

    mock_tokenized = NormalizedTokenizedEquityQuote(
        symbol="xGOOGL",
        display_symbol="xGOOGL/USDT",
        name="xGOOGL (Alphabet Inc.)",
        asset_type="tokenized_equity",
        provider="OKX",
        provider_symbol="XGOOGL-USDT",
        underlying_symbol="GOOGL",
        underlying_name="Alphabet Inc.",
        price="340.28",
        open_24h="335.00",
        high_24h="342.00",
        low_24h="334.50",
        volume_24h="1250",
        quote_volume_24h="425350",
        change_24h_abs="+5.28",
        change_24h_pct=1.58,
        quote_currency="USDT",
        tokenized_label="Tokenized Equity • OKX",
        timestamp=datetime.now(timezone.utc),
        data_status="live"
    )

    with patch.object(service.equity_provider, "get_quote", return_value=unconfigured_equity), \
         patch.object(service.tokenized_provider, "get_tokenized_quote", return_value=mock_tokenized), \
         patch("app.modules.market_data.service.global_cache.get", return_value=None):
        
        comp = await service.compare_equity("GOOGL")

    assert comp.underlying_symbol == "GOOGL"
    assert comp.comparison_available is False
    assert "Finnhub" in comp.unavailability_reason
    assert comp.price_difference_abs is None
    assert comp.price_difference_pct is None

def test_api_get_supported_assets_with_type_filter():
    """Verify GET /api/v1/markets/assets filter by category"""
    resp_all = client.get("/api/v1/markets/assets")
    assert resp_all.status_code == 200
    all_items = resp_all.json()
    assert len(all_items) >= 10

    resp_equity = client.get("/api/v1/markets/assets?type=equity")
    assert resp_equity.status_code == 200
    equity_items = resp_equity.json()
    assert all(item["category"] == "equity" for item in equity_items)

    resp_crypto = client.get("/api/v1/markets/assets?type=crypto")
    assert resp_crypto.status_code == 200
    crypto_items = resp_crypto.json()
    assert all(item["category"] == "crypto" for item in crypto_items)

def test_api_get_equities_endpoint():
    """Verify GET /api/v1/markets/equities returns quote list with provenance"""
    resp = client.get("/api/v1/markets/equities")
    assert resp.status_code == 200
    quotes = resp.json()
    assert len(quotes) >= 10
    for q in quotes:
        assert "data_status" in q
        assert q["data_status"] in ["live", "cached", "provider_not_configured", "unavailable"]

def test_api_btc_candles_endpoint():
    """Verify GET /api/v1/markets/BTC/candles returns 200 and candle list"""
    resp = client.get("/api/v1/markets/BTC/candles?timeframe=1H&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC"
    assert "candles" in data
    assert isinstance(data["candles"], list)
