import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.modules.portfolio.okx_account import OKXAccountClient
from app.modules.portfolio.service import PortfolioService
from app.modules.market_data.schemas import NormalizedTicker
from app.modules.market_data.cache import global_cache

client = TestClient(app)

MOCK_TRADING_BALANCES = [
    {"currency": "BTC", "balance": "0.5", "available": "0.5", "frozen": "0.0", "source": "Trading"},
    {"currency": "USDT", "balance": "1000.0", "available": "1000.0", "frozen": "0.0", "source": "Trading"}
]

MOCK_FUNDING_BALANCES = [
    {"currency": "BTC", "balance": "0.25", "available": "0.25", "frozen": "0.0", "source": "Funding"},
    {"currency": "ETH", "balance": "2.0", "available": "2.0", "frozen": "0.0", "source": "Funding"},
    {"currency": "UNKNOWNCOIN", "balance": "100.0", "available": "100.0", "frozen": "0.0", "source": "Funding"}
]

@pytest.fixture(autouse=True)
def clear_cache():
    asyncio.run(global_cache.clear())

def test_unconfigured_portfolio_status():
    with patch.object(OKXAccountClient, "is_configured", return_value=False):
        response = client.get("/api/v1/portfolio/status")
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is False
        assert data["provider"] == "OKX"
        assert data["connection_status"] == "unconfigured"
        # Security audit: ensure no secret fields leak
        assert "api_key" not in data
        assert "api_secret" not in data
        assert "passphrase" not in data
        assert "OK-ACCESS-KEY" not in data

def test_unconfigured_portfolio_summary():
    with patch.object(OKXAccountClient, "is_configured", return_value=False):
        response = client.get("/api/v1/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert data["data_status"] == "unconfigured"
        assert data["total_value_usdt"] == "0.00"
        assert len(data["assets"]) == 0

def test_deterministic_signing_logic():
    client_obj = OKXAccountClient(api_key="test_key", api_secret="test_secret", passphrase="test_pass")
    timestamp = "2026-08-20T21:00:00.000Z"
    method = "GET"
    request_path = "/api/v5/account/balance"
    signature = client_obj._generate_signature(timestamp, method, request_path)
    assert isinstance(signature, str)
    assert len(signature) > 0
    # Re-running with exact parameters yields identical signature
    sig2 = client_obj._generate_signature(timestamp, method, request_path)
    assert signature == sig2

@patch.object(OKXAccountClient, "is_configured", return_value=True)
@patch.object(OKXAccountClient, "fetch_trading_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_funding_balances", new_callable=AsyncMock)
@patch("app.modules.portfolio.service.MarketDataService.get_ticker", new_callable=AsyncMock)
def test_configured_portfolio_summary_mocked(mock_get_ticker, mock_funding, mock_trading, mock_is_config):
    mock_trading.return_value = MOCK_TRADING_BALANCES
    mock_funding.return_value = MOCK_FUNDING_BALANCES

    # Mock market prices: BTC=$60,000, ETH=$3,000
    def side_effect(symbol):
        if symbol == "BTC":
            return NormalizedTicker(
                symbol="BTC", provider_symbol="BTC-USDT", name="Bitcoin",
                price="60000.00", open_24h="59000.00", high_24h="61000.00", low_24h="58000.00",
                volume_24h="100.0", quote_volume_24h="6000000.0", change_24h_abs="+1000.00",
                change_24h_pct=1.69, timestamp="2026-08-20T21:00:00Z", provider="OKX"
            )
        elif symbol == "ETH":
            return NormalizedTicker(
                symbol="ETH", provider_symbol="ETH-USDT", name="Ethereum",
                price="3000.00", open_24h="2950.00", high_24h="3050.00", low_24h="2900.00",
                volume_24h="500.0", quote_volume_24h="1500000.0", change_24h_abs="+50.00",
                change_24h_pct=1.69, timestamp="2026-08-20T21:00:00Z", provider="OKX"
            )
        raise ValueError(f"No ticker for {symbol}")

    mock_get_ticker.side_effect = side_effect

    service = PortfolioService(
        account_client=OKXAccountClient(api_key="k", api_secret="s", passphrase="p")
    )
    
    summary = asyncio.run(service.get_portfolio_summary())

    assert summary.data_status == "configured"
    assert summary.asset_count == 4
    # Calculation:
    # BTC total = 0.5 (Trading) + 0.25 (Funding) = 0.75 BTC * $60,000 = $45,000
    # ETH total = 2.0 ETH * $3,000 = $6,000
    # USDT total = 1000.0 * $1 = $1,000
    # UNKNOWNCOIN = 100.0 balance, valuation_available=False, price=None, est_value=None
    # Total Portfolio = $52,000
    assert summary.total_value_usdt == "52000.00"

    btc_asset = next(a for a in summary.assets if a.symbol == "BTC")
    assert btc_asset.total_balance == "0.75"
    assert len(btc_asset.account_sources) == 2
    assert btc_asset.estimated_value_usdt == "45000.00"
    assert btc_asset.allocation_pct == 86.54  # (45000 / 52000) * 100

    unknown_asset = next(a for a in summary.assets if a.symbol == "UNKNOWNCOIN")
    assert unknown_asset.valuation_available is False
    assert unknown_asset.price_usdt is None
    assert unknown_asset.estimated_value_usdt is None
    assert unknown_asset.total_balance == "100"

def test_account_sources_endpoint():
    response = client.get("/api/v1/portfolio/accounts")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "OKX"
    assert "Trading" in data["sources"]
    assert "Funding" in data["sources"]

@patch.object(OKXAccountClient, "is_configured", return_value=True)
@patch.object(OKXAccountClient, "fetch_trading_balances", side_effect=RuntimeError("OKX API HTTP error status 401"))
def test_invalid_credentials_error_handling(mock_trading, mock_is_config):
    service = PortfolioService(
        account_client=OKXAccountClient(api_key="bad_k", api_secret="bad_s", passphrase="bad_p")
    )
    summary = asyncio.run(service.get_portfolio_summary())
    assert summary.data_status == "error"
    assert "Failed to sync OKX portfolio" in summary.error_message
    assert summary.total_value_usdt == "0.00"

def test_public_market_api_isolation():
    # Verify public market health and tickers remain completely unaffected by portfolio configuration
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"
