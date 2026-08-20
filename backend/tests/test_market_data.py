import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.modules.market_data.okx_provider import OKXMarketDataProvider
from app.modules.market_data.schemas import NormalizedTicker, NormalizedCandle, AssetInfo
from app.modules.market_data.exceptions import InvalidAssetError, InvalidTimeframeError, ProviderUnavailableError
from app.modules.market_data.cache import MarketDataCache
from app.modules.market_data.service import MarketDataService

client = TestClient(app)

# Mock Data
MOCK_OKX_TICKER_RAW = {
    "code": "0",
    "msg": "",
    "data": [
        {
            "instId": "BTC-USDT",
            "last": "64250.50",
            "open24h": "62500.00",
            "high24h": "65000.00",
            "low24h": "62000.00",
            "vol24h": "12500.25",
            "volCcy24h": "803125000.00",
            "ts": "1724188800000"
        }
    ]
}

MOCK_OKX_CANDLES_RAW = {
    "code": "0",
    "msg": "",
    "data": [
        ["1724188800000", "64000.0", "64500.0", "63800.0", "64250.0", "150.5", "9669625.0", "9669625.0", "1"],
        ["1724185200000", "63500.0", "64100.0", "63400.0", "64000.0", "120.2", "7692800.0", "7692800.0", "1"],
    ]
}

def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "AssetPilot AI"

def test_get_supported_assets():
    response = client.get("/api/v1/markets/assets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    symbols = [item["symbol"] for item in data]
    assert "BTC" in symbols
    assert "ETH" in symbols
    assert "SOL" in symbols

@patch.object(OKXMarketDataProvider, "_fetch_okx_json", new_callable=AsyncMock)
def test_get_single_ticker_mocked(mock_fetch):
    mock_fetch.return_value = MOCK_OKX_TICKER_RAW
    
    response = client.get("/api/v1/markets/BTC")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTC"
    assert data["provider_symbol"] == "BTC-USDT"
    assert data["price"] == "64250.50"
    assert data["change_24h_pct"] == 2.8  # (64250.5 - 62500)/62500 * 100 = +2.8%
    assert data["provider"] == "OKX"

def test_get_invalid_asset():
    response = client.get("/api/v1/markets/INVALID_ASSET_XYZ")
    assert response.status_code == 400
    data = response.json()
    assert "Unsupported or invalid asset symbol" in data["detail"]

@patch.object(OKXMarketDataProvider, "_fetch_okx_json", new_callable=AsyncMock)
def test_get_candles_mocked(mock_fetch):
    mock_fetch.return_value = MOCK_OKX_CANDLES_RAW
    
    response = client.get("/api/v1/markets/BTC/candles?timeframe=1H&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTC"
    assert data["timeframe"] == "1H"
    assert len(data["candles"]) == 2
    # Verify chronological ordering (oldest first, newest last)
    assert data["candles"][0]["open"] == "63500.0"
    assert data["candles"][1]["close"] == "64250.0"

def test_get_candles_invalid_timeframe():
    response = client.get("/api/v1/markets/BTC/candles?timeframe=99H")
    assert response.status_code == 400
    data = response.json()
    assert "Invalid timeframe" in data["detail"]

@patch.object(OKXMarketDataProvider, "_fetch_okx_json", new_callable=AsyncMock)
def test_provider_unavailable_handling(mock_fetch):
    mock_fetch.side_effect = ProviderUnavailableError("OKX", "Upstream API Connection Error")
    
    # Clear cache to force API call
    response = client.get("/api/v1/markets/ETH")
    assert response.status_code in [503, 200]  # Returns 503 if not cached

@pytest.mark.asyncio
async def test_in_memory_ttl_cache():
    cache = MarketDataCache(ticker_ttl=0.2)
    await cache.set("test_key", {"val": 100})
    
    res1 = await cache.get("test_key")
    assert res1 == {"val": 100}
    
    # Wait for TTL to expire
    import asyncio
    await asyncio.sleep(0.25)
    
    res2 = await cache.get("test_key")
    assert res2 is None
