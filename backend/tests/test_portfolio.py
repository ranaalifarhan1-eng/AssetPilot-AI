import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.modules.portfolio.okx_account import OKXAccountClient
from app.modules.portfolio.service import PortfolioService
from app.modules.portfolio.schemas import PortfolioSummary, PortfolioAsset
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
]

MOCK_EARN_BALANCES = [
    {"currency": "USDT", "balance": "500.0", "available": "500.0", "frozen": "0.0", "source": "Earn"}
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
        assert data["valuation_status"] == "unconfigured"
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
    sig2 = client_obj._generate_signature(timestamp, method, request_path)
    assert signature == sig2

@patch.object(OKXAccountClient, "is_configured", return_value=True)
@patch.object(OKXAccountClient, "fetch_trading_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_funding_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_earn_balances", new_callable=AsyncMock)
@patch("app.modules.portfolio.service.MarketDataService.get_ticker", new_callable=AsyncMock)
def test_case_a_same_balances_live_prices_complete(mock_get_ticker, mock_earn, mock_funding, mock_trading, mock_is_config):
    """Case A: All assets priced with live data -> valuation_status is 'complete'."""
    mock_trading.return_value = MOCK_TRADING_BALANCES
    mock_funding.return_value = MOCK_FUNDING_BALANCES
    mock_earn.return_value = MOCK_EARN_BALANCES

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
    assert summary.valuation_status == "complete"
    assert summary.valuation_complete is True
    assert summary.stale_assets == []
    assert summary.unvalued_assets == []
    assert summary.total_value_usdt == "52500.00"

    btc_asset = next(a for a in summary.assets if a.symbol == "BTC")
    assert btc_asset.price_status == "live"
    assert btc_asset.estimated_value_usdt == "45000.00"

@patch.object(OKXAccountClient, "is_configured", return_value=True)
@patch.object(OKXAccountClient, "fetch_trading_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_funding_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_earn_balances", new_callable=AsyncMock)
@patch("app.modules.portfolio.service.MarketDataService.get_ticker", new_callable=AsyncMock)
def test_case_b_same_balances_transient_failure_recent_known_good_price(mock_get_ticker, mock_earn, mock_funding, mock_trading, mock_is_config):
    """Case B: Same balances + transient price failure + recent known-good price -> stale_complete."""
    mock_trading.return_value = [{"currency": "BTC", "balance": "1.0", "available": "1.0", "frozen": "0.0", "source": "Trading"}]
    mock_funding.return_value = [{"currency": "USDT", "balance": "50.0", "available": "50.0", "frozen": "0.0", "source": "Funding"}]
    mock_earn.return_value = []

    # Step 1: establish live price in cache
    mock_get_ticker.return_value = NormalizedTicker(
        symbol="BTC", provider_symbol="BTC-USDT", name="Bitcoin",
        price="70000.00", open_24h="69000.00", high_24h="71000.00", low_24h="68000.00",
        volume_24h="10.0", quote_volume_24h="700000.0", change_24h_abs="+1000.00",
        change_24h_pct=1.45, timestamp="2026-08-20T21:00:00Z", provider="OKX"
    )

    service = PortfolioService(
        account_client=OKXAccountClient(api_key="k", api_secret="s", passphrase="p")
    )
    summary1 = asyncio.run(service.get_portfolio_summary())
    assert summary1.valuation_status == "complete"

    # Invalidate latest portfolio snapshot cache
    asyncio.run(global_cache.delete("portfolio_summary"))

    # Step 2: live lookup fails -> falls back to recent known-good price ($70,000)
    mock_get_ticker.side_effect = RuntimeError("OKX Ticker Timeout")
    summary2 = asyncio.run(service.get_portfolio_summary())

    assert summary2.valuation_status == "stale_complete"
    assert summary2.valuation_complete is False
    assert "BTC" in summary2.stale_assets
    assert summary2.unvalued_assets == []
    # 1.0 BTC * $70,000 + $50 USDT = $70,050.00
    assert summary2.total_value_usdt == "70050.00"

    btc_asset = next(a for a in summary2.assets if a.symbol == "BTC")
    assert btc_asset.price_status == "stale"
    assert btc_asset.price_usdt == "70000.00"
    assert btc_asset.estimated_value_usdt == "70000.00"

@patch.object(OKXAccountClient, "is_configured", return_value=True)
@patch.object(OKXAccountClient, "fetch_trading_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_funding_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_earn_balances", new_callable=AsyncMock)
@patch("app.modules.portfolio.service.MarketDataService.get_ticker", new_callable=AsyncMock)
def test_case_c_balance_changes_recalculated_with_stale_price_never_reuses_old_total(mock_get_ticker, mock_earn, mock_funding, mock_trading, mock_is_config):
    """
    Case C (CRITICAL): User deposits additional BTC (0.5 -> 1.5 BTC).
    Live BTC price fails.
    Verify valuation uses NEW balance (1.5 BTC) * last-known-good price ($60,000) = $90,000 (+ $1000 USDT = $91,000),
    and does NOT blindly reuse the old $31,000 total!
    """
    # Step 1: Initial balance is 0.5 BTC + $1000 USDT -> total $31,000
    mock_trading.return_value = [
        {"currency": "BTC", "balance": "0.5", "available": "0.5", "frozen": "0.0", "source": "Trading"},
        {"currency": "USDT", "balance": "1000.0", "available": "1000.0", "frozen": "0.0", "source": "Trading"}
    ]
    mock_funding.return_value = []
    mock_earn.return_value = []

    mock_get_ticker.return_value = NormalizedTicker(
        symbol="BTC", provider_symbol="BTC-USDT", name="Bitcoin",
        price="60000.00", open_24h="59000.00", high_24h="61000.00", low_24h="58000.00",
        volume_24h="100.0", quote_volume_24h="6000000.0", change_24h_abs="+1000.00",
        change_24h_pct=1.69, timestamp="2026-08-20T21:00:00Z", provider="OKX"
    )

    service = PortfolioService(
        account_client=OKXAccountClient(api_key="k", api_secret="s", passphrase="p")
    )
    summary_old = asyncio.run(service.get_portfolio_summary())
    assert summary_old.total_value_usdt == "31000.00"

    # Step 2: User deposits 1.0 more BTC -> total balance is now 1.5 BTC!
    asyncio.run(global_cache.delete("portfolio_summary"))
    mock_trading.return_value = [
        {"currency": "BTC", "balance": "1.5", "available": "1.5", "frozen": "0.0", "source": "Trading"},
        {"currency": "USDT", "balance": "1000.0", "available": "1000.0", "frozen": "0.0", "source": "Trading"}
    ]

    # Live price fails
    mock_get_ticker.side_effect = RuntimeError("OKX network error")

    summary_new = asyncio.run(service.get_portfolio_summary())

    # MUST dynamically calculate: 1.5 BTC * $60,000 + $1000 = $91,000.00 (NOT $31,000.00!)
    assert summary_new.total_value_usdt == "91000.00"
    assert summary_new.valuation_status == "stale_complete"
    assert "BTC" in summary_new.stale_assets

    btc_asset = next(a for a in summary_new.assets if a.symbol == "BTC")
    assert btc_asset.total_balance == "1.5"
    assert btc_asset.price_status == "stale"
    assert btc_asset.estimated_value_usdt == "90000.00"

@patch.object(OKXAccountClient, "is_configured", return_value=True)
@patch.object(OKXAccountClient, "fetch_trading_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_funding_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_earn_balances", new_callable=AsyncMock)
@patch("app.modules.portfolio.service.MarketDataService.get_ticker", new_callable=AsyncMock)
def test_case_d_balance_changes_no_known_good_price_partial(mock_get_ticker, mock_earn, mock_funding, mock_trading, mock_is_config):
    """Case D: Balance changes + no known-good price -> valuation_status is 'partial'."""
    mock_trading.return_value = [{"currency": "NEWCOIN", "balance": "50.0", "available": "50.0", "frozen": "0.0", "source": "Trading"}]
    mock_funding.return_value = [{"currency": "USDT", "balance": "20.0", "available": "20.0", "frozen": "0.0", "source": "Funding"}]
    mock_earn.return_value = []

    mock_get_ticker.side_effect = ValueError("No ticker available")

    service = PortfolioService(
        account_client=OKXAccountClient(api_key="k", api_secret="s", passphrase="p")
    )
    summary = asyncio.run(service.get_portfolio_summary())

    assert summary.valuation_status == "partial"
    assert summary.valuation_complete is False
    assert "NEWCOIN" in summary.unvalued_assets
    assert summary.total_value_usdt == "20.00"
    assert summary.known_value_usdt == "20.00"

@patch.object(OKXAccountClient, "is_configured", return_value=True)
@patch.object(OKXAccountClient, "fetch_trading_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_funding_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_earn_balances", new_callable=AsyncMock)
@patch("app.modules.portfolio.service.MarketDataService.get_ticker", new_callable=AsyncMock)
def test_case_e_known_good_price_exceeds_permitted_stale_window_becomes_partial(mock_get_ticker, mock_earn, mock_funding, mock_trading, mock_is_config):
    """Case E: Known-good price is older than 900s staleness window -> asset becomes unvalued, status is 'partial'."""
    mock_trading.return_value = [{"currency": "BTC", "balance": "1.0", "available": "1.0", "frozen": "0.0", "source": "Trading"}]
    mock_funding.return_value = [{"currency": "USDT", "balance": "100.0", "available": "100.0", "frozen": "0.0", "source": "Funding"}]
    mock_earn.return_value = []

    # Manually seed price cache with an expired price timestamp (20 minutes ago > 15 min limit)
    old_time = datetime.now(timezone.utc) - timedelta(minutes=20)
    asyncio.run(global_cache.set("last_known_price:BTC", {"price": "65000.00", "as_of": old_time}, ttl=3600.0))

    # Live ticker fails
    mock_get_ticker.side_effect = RuntimeError("OKX network error")

    service = PortfolioService(
        account_client=OKXAccountClient(api_key="k", api_secret="s", passphrase="p")
    )
    summary = asyncio.run(service.get_portfolio_summary())

    # Expired price MUST be rejected -> partial status!
    assert summary.valuation_status == "partial"
    assert summary.valuation_complete is False
    assert "BTC" in summary.unvalued_assets
    assert summary.total_value_usdt == "100.00"

@patch.object(OKXAccountClient, "is_configured", return_value=True)
@patch.object(OKXAccountClient, "fetch_trading_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_funding_balances", new_callable=AsyncMock)
@patch.object(OKXAccountClient, "fetch_earn_balances", new_callable=AsyncMock)
@patch("app.modules.portfolio.service.MarketDataService.get_ticker", new_callable=AsyncMock)
def test_case_f_provider_recovers_automatically_returns_complete(mock_get_ticker, mock_earn, mock_funding, mock_trading, mock_is_config):
    """Case F: When provider recovers, portfolio automatically transitions from stale_complete back to complete."""
    mock_trading.return_value = [{"currency": "BTC", "balance": "1.0", "available": "1.0", "frozen": "0.0", "source": "Trading"}]
    mock_funding.return_value = []
    mock_earn.return_value = []

    # Seed fresh price
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=2)
    asyncio.run(global_cache.set("last_known_price:BTC", {"price": "68000.00", "as_of": recent_time}, ttl=3600.0))

    service = PortfolioService(
        account_client=OKXAccountClient(api_key="k", api_secret="s", passphrase="p")
    )

    # 1. Price fails -> stale_complete
    mock_get_ticker.side_effect = RuntimeError("Temporary outage")
    summary1 = asyncio.run(service.get_portfolio_summary())
    assert summary1.valuation_status == "stale_complete"

    # 2. Provider recovers with fresh $75,000 price
    asyncio.run(global_cache.delete("portfolio_summary"))
    mock_get_ticker.side_effect = None
    mock_get_ticker.return_value = NormalizedTicker(
        symbol="BTC", provider_symbol="BTC-USDT", name="Bitcoin",
        price="75000.00", open_24h="70000.00", high_24h="76000.00", low_24h="69000.00",
        volume_24h="100.0", quote_volume_24h="7500000.0", change_24h_abs="+5000.00",
        change_24h_pct=7.14, timestamp="2026-08-20T21:00:00Z", provider="OKX"
    )

    summary2 = asyncio.run(service.get_portfolio_summary())
    assert summary2.valuation_status == "complete"
    assert summary2.valuation_complete is True
    assert summary2.total_value_usdt == "75000.00"
    assert summary2.stale_assets == []

def test_account_sources_endpoint():
    response = client.get("/api/v1/portfolio/accounts")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "OKX"
    assert "Trading" in data["sources"]
    assert "Funding" in data["sources"]
    assert "Earn" in data["sources"]

@patch.object(OKXAccountClient, "is_configured", return_value=True)
@patch.object(OKXAccountClient, "fetch_trading_balances", side_effect=RuntimeError("OKX API HTTP error status 401"))
def test_invalid_credentials_error_handling(mock_trading, mock_is_config):
    service = PortfolioService(
        account_client=OKXAccountClient(api_key="bad_k", api_secret="bad_s", passphrase="bad_p")
    )
    summary = asyncio.run(service.get_portfolio_summary())
    assert summary.data_status == "error"
    assert summary.valuation_status == "error"
    assert "Failed to sync OKX portfolio" in summary.error_message
    assert summary.total_value_usdt == "0.00"

def test_public_market_api_isolation():
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"
