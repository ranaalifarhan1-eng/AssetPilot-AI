import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
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
async def test_finnhub_provider_supported_equities():
    """Verify supported traditional equities universe contains core US stocks"""
    provider = FinnhubEquityProvider()
    equities = await provider.get_supported_equities()
    assert len(equities) >= 10
    symbols = [e.symbol for e in equities]
    assert "AAPL" in symbols
    assert "GOOGL" in symbols
    assert "MSFT" in symbols
    assert "NVDA" in symbols
    assert "TSLA" in symbols
    for e in equities:
        assert e.category == "equity"
        assert e.quote_currency == "USD"
        assert e.venue == "NASDAQ"

@pytest.mark.asyncio
async def test_finnhub_provider_reference_quote():
    """Verify deterministic equity quote structure in reference mode"""
    provider = FinnhubEquityProvider(api_key="")
    quote = await provider.get_quote("GOOGL")
    assert quote.symbol == "GOOGL"
    assert quote.name == "Alphabet Inc."
    assert quote.asset_type == "equity"
    assert Decimal(quote.price) > 0
    assert quote.currency == "USD"

@pytest.mark.asyncio
async def test_okx_tokenized_instrument_filtering():
    """Verify dynamic discovery includes valid xStocks and excludes non-equity tokens"""
    mock_instruments_data = [
        {"instId": "XGOOGL-USDT", "instType": "SPOT"},
        {"instId": "XAAPL-USDT", "instType": "SPOT"},
        {"instId": "XMSTR-USDT", "instType": "SPOT"},
        {"instId": "XRP-USDT", "instType": "SPOT"},  # Non-equity token, must be ignored
        {"instId": "XLM-USDT", "instType": "SPOT"},  # Non-equity token, must be ignored
        {"instId": "BTC-USDT", "instType": "SPOT"},  # Normal crypto, ignored
    ]

    provider = OKXTokenizedStocksProvider()
    with patch.object(provider, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_resp = AsyncMock()
        mock_resp.json.return_value = {"code": "0", "data": mock_instruments_data}
        mock_resp.raise_for_status = lambda: None
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
async def test_equity_comparison_logic():
    """Verify underlying vs tokenized price comparison and difference calculation"""
    service = MarketDataService()

    mock_equity = NormalizedEquityQuote(
        symbol="GOOGL",
        name="Alphabet Inc.",
        asset_type="equity",
        provider="Finnhub",
        price="180.00",
        change_abs="+1.00",
        change_pct=0.56,
        currency="USD",
        market_timestamp=datetime.now(timezone.utc),
        market_state="open"
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
        price="181.80",
        open_24h="180.00",
        high_24h="182.00",
        low_24h="179.00",
        volume_24h="1000",
        quote_volume_24h="181800",
        change_24h_abs="+1.80",
        change_24h_pct=1.00,
        quote_currency="USDT",
        tokenized_label="Tokenized Equity • OKX",
        timestamp=datetime.now(timezone.utc)
    )

    with patch.object(service.equity_provider, "get_quote", return_value=mock_equity), \
         patch.object(service.tokenized_provider, "get_tokenized_quote", return_value=mock_tokenized), \
         patch("app.modules.market_data.service.global_cache.get", return_value=None):
        
        comp = await service.compare_equity("GOOGL")

    assert comp.underlying_symbol == "GOOGL"
    assert comp.underlying_price == "180.00"
    assert comp.tokenized_counterpart_available is True
    assert comp.tokenized_symbol == "xGOOGL"
    assert comp.tokenized_price == "181.80"
    assert comp.price_difference_abs == "+1.80"
    assert comp.price_difference_pct == 1.0
    assert comp.comparison_label == "Reference Price Difference"
    assert "Not an arbitrage signal" in comp.disclaimer

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
    """Verify GET /api/v1/markets/equities returns quote list"""
    resp = client.get("/api/v1/markets/equities")
    assert resp.status_code == 200
    quotes = resp.json()
    assert len(quotes) >= 10
    symbols = [q["symbol"] for q in quotes]
    assert "AAPL" in symbols
    assert "NVDA" in symbols

def test_api_get_single_equity_endpoint():
    """Verify GET /api/v1/markets/equities/AAPL"""
    resp = client.get("/api/v1/markets/equities/AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["asset_type"] == "equity"
    assert float(data["price"]) > 0

def test_api_get_equity_comparison_endpoint():
    """Verify GET /api/v1/markets/equity-comparison/NVDA"""
    resp = client.get("/api/v1/markets/equity-comparison/NVDA")
    assert resp.status_code == 200
    data = resp.json()
    assert data["underlying_symbol"] == "NVDA"
    assert data["comparison_label"] == "Reference Price Difference"
    assert "disclaimer" in data
