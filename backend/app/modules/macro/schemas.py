from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class EconomicEvent(BaseModel):
    id: str = Field(..., description="Unique deterministic event identifier")
    provider: str = Field(..., description="Data provider / publisher")
    source: str = Field(..., description="Authoritative primary source (e.g. Federal Reserve, BLS, BEA, Treasury, DOL)")
    source_url: Optional[str] = Field(None, description="Official URL for release or schedule")
    
    # Official Release vs Extracted Indicator distinction
    release_name: str = Field(..., description="Official statistical release name (e.g. 'Personal Income and Outlays', 'Gross Domestic Product')")
    indicator_name: str = Field(..., description="Extracted economic indicator (e.g. 'Core PCE Price Index (YoY)', 'GDP (QoQ Second Estimate)')")
    event_name: str = Field(..., description="Display title for UI (e.g. 'Core PCE Price Index (YoY)')")
    event_code: str = Field(..., description="Standardized event code (e.g. FED_RATE, CPI_YOY, NFP, GDP_QOQ, PCE_CORE_YOY)")
    category: str = Field(..., description="Category: 'Monetary Policy', 'Inflation', 'Labor', 'Growth', 'Liquidity / Rates'")
    country: str = Field("US", description="Country code (e.g. US)")
    currency: str = Field("USD", description="Currency code (e.g. USD)")
    
    scheduled_at: datetime = Field(..., description="Scheduled release timestamp in UTC (timezone-aware)")
    period: Optional[str] = Field(None, description="Economic observation period (e.g. 'Jul 2026', 'Q2 2026')")
    
    actual: Optional[float] = Field(None, description="Actual released figure, or null if upcoming")
    forecast: Optional[float] = Field(None, description="Consensus estimate / forecast from verified provider, or null if unavailable")
    previous: Optional[float] = Field(None, description="Previous period figure, or null if unavailable")
    unit: str = Field("%", description="Unit of measurement (e.g. '%', 'k', 'bps', 'B')")
    importance: str = Field("high", description="Importance level: 'high', 'medium', 'low'")
    event_status: str = Field("upcoming", description="Status: 'upcoming', 'released', 'revised', 'delayed', 'cancelled', 'unknown'")
    
    surprise_absolute: Optional[float] = Field(None, description="actual - forecast (strictly null if forecast is null)")
    surprise_percentage: Optional[float] = Field(None, description="(actual - forecast) / abs(forecast) * 100 (strictly null if forecast is null or 0)")
    interpretation_direction: Optional[str] = Field(None, description="Deterministic economic interpretation (e.g. Higher than Forecast / Inflationary)")
    market_impact_summary: Optional[str] = Field(None, description="Informational summary of market implications")
    
    # Explicit Field-Level Provenance
    schedule_source: Optional[str] = Field(None, description="Source agency providing the scheduled date")
    schedule_source_url: Optional[str] = Field(None, description="URL where release schedule is officially published")
    schedule_status: str = Field("unavailable", description="Schedule provenance: live, cached, fallback, unavailable")
    schedule_retrieved_at: Optional[datetime] = None
    forecast_source: Optional[str] = Field(None, description="Verified provider of consensus forecast (null if none)")
    forecast_source_url: Optional[str] = Field(None, description="URL of forecast provider")
    actual_source: Optional[str] = Field(None, description="Primary source providing the actual release figure")
    actual_source_url: Optional[str] = Field(None, description="URL where actual figure was officially released")
    actual_status: str = Field("unavailable", description="Actual-value provenance: live, cached, fallback, unavailable")
    actual_retrieved_at: Optional[datetime] = None
    previous_source: Optional[str] = Field(None, description="Primary source for previous period figure")
    previous_source_url: Optional[str] = Field(None, description="URL for previous period release")
    previous_status: str = Field("unavailable", description="Previous-value provenance: live, cached, fallback, unavailable")
    previous_retrieved_at: Optional[datetime] = None
    forecast_status: str = Field("unavailable", description="Forecast provenance: live, cached, fallback, unavailable")
    forecast_retrieved_at: Optional[datetime] = None
    
    related_assets: List[str] = Field(default_factory=list, description="Broad market assets exposed (e.g. BTC, ETH, US Equities, xStocks)")
    portfolio_exposure: List[str] = Field(default_factory=list, description="Intersection of related assets with user's active portfolio")
    retrieved_at: datetime = Field(..., description="Timestamp when event data was collected in UTC")
    data_status: str = Field("live", description="Status: 'live', 'cached', 'stale', 'unavailable', 'provider_not_configured'")

class YieldCurveData(BaseModel):
    date: str = Field(..., description="Observation date (YYYY-MM-DD)")
    rates: Dict[str, float] = Field(default_factory=dict, description="Benchmark yield rates by tenor: 1M, 2M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y")
    spread_10y_2y_bps: float = Field(0.0, description="10Y minus 2Y spread in basis points (100 bps = 1.00%)")
    curve_inversion: bool = Field(False, description="True if 2Y yield > 10Y yield (inverted yield curve indicator)")
    source: str = Field("U.S. Department of the Treasury", description="Official data publisher")
    source_url: str = Field(
        "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026",
        description="Official Treasury XML endpoint"
    )
    retrieved_at: datetime = Field(..., description="Timestamp of retrieval in UTC")

class MacroStatusResponse(BaseModel):
    service: str = "Macro & Economic Events Intelligence"
    status: str = "ok"
    providers_configured: List[str] = Field(default_factory=list, description="Active authoritative macro sources")
    total_events_tracked: int = Field(0, description="Total active events in calendar and recent history")
    upcoming_events_count: int = Field(0, description="Count of upcoming scheduled macro events")
    recent_events_count: int = Field(0, description="Count of released macro events")
    last_collection_at: Optional[datetime] = Field(None, description="Last successful macro sync timestamp")
    yield_curve_date: Optional[str] = Field(None, description="Date of latest Treasury yield curve observation")
