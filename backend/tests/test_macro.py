import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.modules.macro.schemas import EconomicEvent, YieldCurveData, MacroStatusResponse
from app.modules.macro.context_engine import MacroContextEngine
from app.modules.macro.providers.fed_provider import FederalReserveProvider
from app.modules.macro.providers.treasury_provider import TreasuryProvider
from app.modules.macro.providers.official_schedule_provider import OfficialScheduleProvider
from app.modules.macro.providers.fred_provider import FREDProvider
from app.modules.macro.service import MacroService
from app.modules.market_data.cache import global_cache
from app.modules.portfolio.schemas import PortfolioSummary, PortfolioAsset

client = TestClient(app)

NY_TZ = ZoneInfo("America/New_York")

@pytest.fixture(autouse=True)
def clear_cache():
    asyncio.run(global_cache.clear())

# --- 1. Deterministic Surprise & Math Engine Tests ---

def test_surprise_calculation_standard():
    # Actual: 3.1%, Forecast: 3.0% -> +0.1pp, +3.33%
    surprise_abs, surprise_pct = MacroContextEngine.calculate_surprises(3.1, 3.0)
    assert surprise_abs == 0.1
    assert surprise_pct == 3.33

def test_surprise_calculation_negative():
    # Actual: 2.7%, Forecast: 2.9% -> -0.2pp, -6.9%
    surprise_abs, surprise_pct = MacroContextEngine.calculate_surprises(2.7, 2.9)
    assert surprise_abs == -0.2
    assert surprise_pct == -6.9

def test_surprise_calculation_null_forecast():
    surprise_abs, surprise_pct = MacroContextEngine.calculate_surprises(2.7, None)
    assert surprise_abs is None
    assert surprise_pct is None

def test_surprise_calculation_null_actual():
    surprise_abs, surprise_pct = MacroContextEngine.calculate_surprises(None, 3.0)
    assert surprise_abs is None
    assert surprise_pct is None

def test_surprise_calculation_zero_forecast_safety():
    # If forecast is 0.0, surprise_pct must safely be None to avoid ZeroDivisionError
    surprise_abs, surprise_pct = MacroContextEngine.calculate_surprises(0.5, 0.0)
    assert surprise_abs == 0.5
    assert surprise_pct is None

# --- 2. Event-Specific Contextual Interpretations ---

def test_cpi_interpretation_higher_than_forecast():
    direction, impact = MacroContextEngine.derive_interpretation(
        event_code="CPI_YOY", category="Inflation", actual=3.2, forecast=3.0, previous=2.9
    )
    assert "Higher Than Forecast" in direction
    assert "Inflationary Pressure" in direction
    assert "headwinds for risk assets" in impact

def test_cpi_interpretation_lower_than_forecast():
    direction, impact = MacroContextEngine.derive_interpretation(
        event_code="CPI_YOY", category="Inflation", actual=2.6, forecast=2.8, previous=2.9
    )
    assert "Lower Than Forecast" in direction
    assert "Disinflationary Progress" in direction
    assert "tailwinds for crypto and equities" in impact

def test_cpi_interpretation_inline():
    direction, impact = MacroContextEngine.derive_interpretation(
        event_code="CPI_YOY", category="Inflation", actual=2.8, forecast=2.8, previous=2.9
    )
    assert "In-Line With Consensus" in direction

def test_fomc_rate_decision_interpretations():
    # Rate hike: 4.50 -> 4.75 (+25 bps)
    dir_hike, imp_hike = MacroContextEngine.derive_interpretation("FED_RATE", "Monetary Policy", 4.75, 4.75, 4.50)
    assert "Interest Rate Hike (+25 bps)" in dir_hike

    # Rate cut: 4.50 -> 4.25 (-25 bps)
    dir_cut, imp_cut = MacroContextEngine.derive_interpretation("FED_RATE", "Monetary Policy", 4.25, 4.25, 4.50)
    assert "Interest Rate Cut (-25 bps)" in dir_cut

    # Rate maintained: 4.50 -> 4.50
    dir_hold, imp_hold = MacroContextEngine.derive_interpretation("FED_RATE", "Monetary Policy", 4.50, 4.50, 4.50)
    assert "Policy Rate Maintained" in dir_hold

def test_nfp_interpretations():
    # Beat
    dir_beat, _ = MacroContextEngine.derive_interpretation("NFP", "Labor", 200.0, 160.0, 150.0)
    assert "Stronger Labor Market" in dir_beat

    # Miss
    dir_miss, _ = MacroContextEngine.derive_interpretation("NFP", "Labor", 120.0, 160.0, 150.0)
    assert "Weaker Labor Market" in dir_miss

# --- 3. Timezone & DST Correctness ---

def test_timezone_dst_conversion_eastern_to_utc():
    # July (Daylight Saving Time EDT, UTC-4): 08:30 EDT -> 12:30 UTC
    dt_summer_ny = datetime(2026, 7, 14, 8, 30, 0, tzinfo=NY_TZ)
    dt_summer_utc = dt_summer_ny.astimezone(timezone.utc)
    assert dt_summer_utc.hour == 12
    assert dt_summer_utc.minute == 30

    # November (Standard Time EST, UTC-5): 08:30 EST -> 13:30 UTC
    dt_winter_ny = datetime(2026, 11, 12, 8, 30, 0, tzinfo=NY_TZ)
    dt_winter_utc = dt_winter_ny.astimezone(timezone.utc)
    assert dt_winter_utc.hour == 13
    assert dt_winter_utc.minute == 30

    # FOMC 14:00 Release
    fomc_july_ny = datetime(2026, 7, 30, 14, 0, 0, tzinfo=NY_TZ)
    assert fomc_july_ny.astimezone(timezone.utc).hour == 18

    fomc_dec_ny = datetime(2026, 12, 17, 14, 0, 0, tzinfo=NY_TZ)
    assert fomc_dec_ny.astimezone(timezone.utc).hour == 19

# --- 4. Portfolio Exposure Mapping ---

@pytest.mark.asyncio
async def test_portfolio_exposure_mapping_with_cached_holdings():
    # Seed cache with user holding BTC and ETH
    mock_summary = PortfolioSummary(
        total_value_usdt="1000.00",
        known_value_usdt="1000.00",
        valuation_status="complete",
        valuation_complete=True,
        assets=[
            PortfolioAsset(
                symbol="BTC", name="Bitcoin", total_balance="0.5", available_balance="0.5",
                frozen_balance="0", account_sources=[], price_usdt="60000", estimated_value_usdt="30000"
            ),
            PortfolioAsset(
                symbol="ETH", name="Ethereum", total_balance="2.0", available_balance="2.0",
                frozen_balance="0", account_sources=[], price_usdt="3000", estimated_value_usdt="6000"
            )
        ]
    )
    await global_cache.set("portfolio_summary", mock_summary)

    service = MacroService()
    events = await service.fetch_and_normalize_all()

    # CPI events are related to BTC and ETH -> portfolio_exposure must contain BTC and ETH
    cpi_event = next((e for e in events if e.event_code == "CPI_YOY"), None)
    assert cpi_event is not None
    assert "BTC" in cpi_event.portfolio_exposure
    assert "ETH" in cpi_event.portfolio_exposure

# --- 5. Provider Isolation & Failure Resilience ---

@pytest.mark.asyncio
async def test_provider_failure_isolation():
    # Mock Fed provider failing, Treasury succeeding
    mock_fed = MagicMock()
    mock_fed.provider_name = "Federal Reserve"
    mock_fed.is_configured.return_value = True
    mock_fed.fetch_events = AsyncMock(side_effect=RuntimeError("Fed RSS Network Timeout"))

    mock_treasury = MagicMock()
    mock_treasury.provider_name = "U.S. Treasury"
    mock_treasury.is_configured.return_value = True
    mock_treasury.fetch_events = AsyncMock(return_value=[
        EconomicEvent(
            id="test-ust-10y", provider="U.S. Treasury", source="U.S. Department of the Treasury",
            event_name="U.S. 10Y Yield", event_code="UST_10Y", category="Liquidity / Rates",
            scheduled_at=datetime.now(timezone.utc), retrieved_at=datetime.now(timezone.utc),
            actual=4.5, unit="%"
        )
    ])

    service = MacroService(providers=[mock_fed, mock_treasury])
    events = await service.fetch_and_normalize_all()

    # Module must NOT crash; Treasury events must be returned safely
    assert len(events) == 1
    assert events[0].id == "test-ust-10y"

# --- 6. Yield Curve Parsing ---

@pytest.mark.asyncio
async def test_yield_curve_calculation():
    provider = TreasuryProvider()
    
    mock_xml = """<feed xmlns="http://www.w3.org/2005/Atom" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices">
        <entry>
            <content type="application/xml">
                <m:properties>
                    <d:NEW_DATE>2026-08-20T00:00:00</d:NEW_DATE>
                    <d:BC_3MONTH>5.15</d:BC_3MONTH>
                    <d:BC_1YEAR>4.28</d:BC_1YEAR>
                    <d:BC_2YEAR>4.06</d:BC_2YEAR>
                    <d:BC_10YEAR>4.29</d:BC_10YEAR>
                    <d:BC_30YEAR>4.55</d:BC_30YEAR>
                </m:properties>
            </content>
        </entry>
    </feed>"""

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = mock_xml.encode("utf-8")
        mock_get.return_value = mock_resp

        curve = await provider.fetch_yield_curve()
        assert curve is not None
        assert curve.date == "2026-08-20"
        assert curve.rates["10Y"] == 4.29
        assert curve.rates["2Y"] == 4.06
        # Spread = (4.29 - 4.06) * 100 = 23.0 bps
        assert curve.spread_10y_2y_bps == 23.0
        assert curve.curve_inversion is False

# --- 7. API Endpoints Tests ---

def test_api_get_macro_status():
    response = client.get("/api/v1/macro/status")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Macro & Economic Events Intelligence"
    assert data["status"] == "ok"
    assert "Federal Reserve" in data["providers_configured"]
    assert "U.S. Treasury" in data["providers_configured"]
    assert data["total_events_tracked"] > 0

def test_api_get_macro_events_filtering():
    # Filter by category = Inflation
    res_inf = client.get("/api/v1/macro/events?category=Inflation")
    assert res_inf.status_code == 200
    inf_events = res_inf.json()
    assert len(inf_events) > 0
    assert all(e["category"] == "Inflation" for e in inf_events)

    # Filter by importance = high
    res_high = client.get("/api/v1/macro/events?importance=high")
    assert res_high.status_code == 200
    high_events = res_high.json()
    assert len(high_events) > 0
    assert all(e["importance"] == "high" for e in high_events)

def test_api_get_upcoming_and_recent():
    res_up = client.get("/api/v1/macro/upcoming?window=30d")
    assert res_up.status_code == 200
    upcoming = res_up.json()
    assert isinstance(upcoming, list)
    if len(upcoming) > 0:
        assert upcoming[0]["event_status"] == "upcoming"

    res_rec = client.get("/api/v1/macro/recent?limit=5")
    assert res_rec.status_code == 200
    recent = res_rec.json()
    assert isinstance(recent, list)
    assert len(recent) <= 5

def test_api_get_single_event_not_found():
    response = client.get("/api/v1/macro/events/non-existent-event-id-xyz")
    assert response.status_code == 404
