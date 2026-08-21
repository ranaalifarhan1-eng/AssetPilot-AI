import pytest
import asyncio
from datetime import datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
    NY_TZ = ZoneInfo("America/New_York")
except Exception:
    NY_TZ = timezone(timedelta(hours=-4))
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.modules.macro.schemas import EconomicEvent, YieldCurveData, MacroStatusResponse
from app.modules.macro.context_engine import MacroContextEngine
from app.modules.macro.providers.fed_provider import FederalReserveProvider, FOMC_SCHEDULE_2026
from app.modules.macro.providers.treasury_provider import TreasuryProvider
from app.modules.macro.providers.official_schedule_provider import OfficialScheduleProvider, OFFICIAL_CALENDAR_2026
from app.modules.macro.providers.fred_provider import FREDProvider
from app.modules.macro.service import MacroService
from app.modules.market_data.cache import global_cache
from app.modules.portfolio.schemas import PortfolioSummary, PortfolioAsset

client = TestClient(app)

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

def test_cpi_interpretation_without_forecast():
    # When forecast is None, it should compare against previous
    direction, impact = MacroContextEngine.derive_interpretation(
        event_code="CPI_YOY", category="Inflation", actual=2.8, forecast=None, previous=2.9
    )
    assert "Decelerating vs Previous Period" in direction

def test_fomc_rate_decision_interpretations():
    # Rate hike: 4.50 -> 4.75 (+25 bps)
    dir_hike, imp_hike = MacroContextEngine.derive_interpretation("FED_RATE", "Monetary Policy", 4.75, None, 4.50)
    assert "Interest Rate Hike (+25 bps)" in dir_hike

    # Rate cut: 4.50 -> 4.25 (-25 bps)
    dir_cut, imp_cut = MacroContextEngine.derive_interpretation("FED_RATE", "Monetary Policy", 4.25, None, 4.50)
    assert "Interest Rate Cut (-25 bps)" in dir_cut

    # Rate maintained: 4.50 -> 4.50
    dir_hold, imp_hold = MacroContextEngine.derive_interpretation("FED_RATE", "Monetary Policy", 4.50, None, 4.50)
    assert "Policy Rate Maintained" in dir_hold

def test_nfp_interpretations_with_forecast():
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

    # FOMC 14:00 Release in EDT (UTC-4 -> 18:00 UTC)
    fomc_july_ny = datetime(2026, 7, 29, 14, 0, 0, tzinfo=NY_TZ)
    assert fomc_july_ny.astimezone(timezone.utc).hour == 18

    # FOMC 14:00 Release in EST (UTC-5 -> 19:00 UTC)
    fomc_dec_ny = datetime(2026, 12, 16, 14, 0, 0, tzinfo=NY_TZ)
    assert fomc_dec_ny.astimezone(timezone.utc).hour == 19

# --- 4. Official BEA / BLS / Fed Schedule Source Truth & Regression Tests ---

@pytest.mark.asyncio
async def test_gdp_schedule_aug_26_source_verification():
    provider = OfficialScheduleProvider()
    events = await provider.fetch_events()

    # Find GDP Q2 2026 Second Estimate
    gdp_event = next((e for e in events if e.event_code == "GDP_QOQ" and "Second" in e.indicator_name), None)
    assert gdp_event is not None
    # Must be August 26, 2026 (NOT Aug 27!)
    assert gdp_event.scheduled_at.year == 2026
    assert gdp_event.scheduled_at.month == 8
    assert gdp_event.scheduled_at.day == 26
    assert gdp_event.scheduled_at.hour == 12  # 8:30 AM EDT -> 12:30 UTC
    assert gdp_event.scheduled_at.minute == 30
    assert gdp_event.release_name == "Gross Domestic Product"
    assert gdp_event.schedule_source == "Bureau of Economic Analysis"
    assert gdp_event.schedule_source_url == "https://www.bea.gov/news/schedule"

@pytest.mark.asyncio
async def test_pce_schedule_aug_26_source_verification():
    provider = OfficialScheduleProvider()
    events = await provider.fetch_events()

    # Find Core PCE for Jul 2026
    pce_event = next((e for e in events if e.event_code == "PCE_CORE_YOY" and e.period == "Jul 2026"), None)
    assert pce_event is not None
    # Must be August 26, 2026 (NOT Aug 28!)
    assert pce_event.scheduled_at.year == 2026
    assert pce_event.scheduled_at.month == 8
    assert pce_event.scheduled_at.day == 26
    assert pce_event.scheduled_at.hour == 12  # 8:30 AM EDT -> 12:30 UTC
    assert pce_event.scheduled_at.minute == 30
    assert pce_event.release_name == "Personal Income and Outlays"
    assert pce_event.indicator_name == "Core PCE Price Index (YoY)"
    assert pce_event.schedule_source == "Bureau of Economic Analysis"

@pytest.mark.asyncio
async def test_forecast_is_null_without_verified_consensus_provider():
    service = MacroService()
    events = await service.fetch_and_normalize_all()

    # All government-scheduled upcoming events must have forecast = None
    upcoming_gov_events = [e for e in events if e.event_status == "upcoming" and e.source in ["Federal Reserve Board", "Bureau of Economic Analysis", "Bureau of Labor Statistics", "Department of Labor"]]
    assert len(upcoming_gov_events) > 0
    for e in upcoming_gov_events:
        assert e.forecast is None, f"Event {e.id} ({e.event_name}) unexpectedly has forecast {e.forecast} without a verified consensus provider"
        assert e.surprise_absolute is None
        assert e.surprise_percentage is None
        assert e.forecast_source is None

@pytest.mark.asyncio
async def test_previous_is_never_substituted_for_forecast():
    provider = OfficialScheduleProvider()
    events = await provider.fetch_events()
    for e in events:
        if e.previous is not None and e.event_status == "upcoming":
            assert e.forecast is None
            assert e.forecast != e.previous

@pytest.mark.asyncio
async def test_fomc_september_date_and_null_forecast():
    provider = FederalReserveProvider()
    events = await provider.fetch_events()
    sep_fomc = next((e for e in events if e.event_code == "FED_RATE" and e.period == "Sep 2026"), None)
    assert sep_fomc is not None
    assert sep_fomc.scheduled_at.year == 2026
    assert sep_fomc.scheduled_at.month == 9
    assert sep_fomc.scheduled_at.day == 16
    assert sep_fomc.scheduled_at.hour == 18  # 14:00 EDT -> 18:00 UTC
    assert sep_fomc.forecast is None
    assert sep_fomc.previous == 4.00

@pytest.mark.asyncio
async def test_jobless_claims_separate_source_and_null_forecast():
    provider = OfficialScheduleProvider()
    events = await provider.fetch_events()
    claims = next((e for e in events if e.event_code == "CLAIMS" and e.period == "Week ending Aug 22"), None)
    assert claims is not None
    assert claims.scheduled_at.day == 27
    assert claims.schedule_source == "Department of Labor"
    assert claims.forecast is None

# --- 5. Portfolio Exposure Mapping ---

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

# --- 6. Provider Isolation & Failure Resilience ---

@pytest.mark.asyncio
async def test_provider_failure_isolation():
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
            release_name="Daily Treasury Rates", indicator_name="U.S. 10Y Yield",
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

# --- 7. Yield Curve Parsing ---

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

# --- 8. API Endpoints Tests ---

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
        # Must have schedule_source
        assert upcoming[0]["schedule_source"] is not None

    res_rec = client.get("/api/v1/macro/recent?limit=5")
    assert res_rec.status_code == 200
    recent = res_rec.json()
    assert isinstance(recent, list)
    assert len(recent) <= 5

def test_api_get_single_event_not_found():
    response = client.get("/api/v1/macro/events/non-existent-event-id-xyz")
    assert response.status_code == 404
