from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MarketEvidence(BaseModel):
    price: Optional[str] = None
    change_24h_pct: Optional[float] = None
    provider: str = "OKX"
    data_status: str = "unavailable"
    as_of: Optional[datetime] = None


class TechnicalEvidence(BaseModel):
    trend: Optional[str] = None
    momentum: Optional[str] = None
    rsi_14: Optional[float] = None
    macd_state: Optional[str] = None
    volatility: Optional[str] = None
    relative_volume: Optional[float] = None
    swing_high: Optional[float] = None
    swing_low: Optional[float] = None
    multi_timeframe_alignment: Optional[str] = None
    data_status: str = "unavailable"
    as_of: Optional[datetime] = None


class ArticleEvidence(BaseModel):
    id: str
    headline: str
    publisher: Optional[str] = None
    url: str
    published_at: datetime
    sentiment: str
    impact: str


class NewsEvidence(BaseModel):
    relevant_story_count: int = 0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    high_impact_count: int = 0
    top_relevant_articles: List[ArticleEvidence] = Field(default_factory=list)
    source_status: str = "unavailable"
    as_of: Optional[datetime] = None


class MacroEventEvidence(BaseModel):
    id: str
    name: str
    scheduled_at: datetime
    importance: str
    data_status: str
    schedule_status: str
    source: str
    source_url: Optional[str] = None


class MacroEvidence(BaseModel):
    next_high_impact_event: Optional[MacroEventEvidence] = None
    days_until_event: Optional[float] = None
    recent_releases: List[MacroEventEvidence] = Field(default_factory=list)
    yield_10y: Optional[float] = None
    curve_spread_bps: Optional[float] = None
    source_status: str = "unavailable"
    as_of: Optional[datetime] = None


class PortfolioEvidence(BaseModel):
    held: Optional[bool] = None
    balance: Optional[str] = None
    estimated_value_usdt: Optional[str] = None
    allocation_pct: Optional[float] = None
    portfolio_valuation_status: str = "unavailable"
    data_status: str = "unavailable"
    as_of: Optional[datetime] = None


class FreshnessEvidence(BaseModel):
    overall_state: str
    stale_components: List[str] = Field(default_factory=list)


class EvidencePackage(BaseModel):
    asset: str
    generated_at: datetime
    market: MarketEvidence
    technical: TechnicalEvidence
    news: NewsEvidence
    macro: MacroEvidence
    portfolio: PortfolioEvidence
    freshness: FreshnessEvidence
    evidence_status: str
    available_components: List[str]
    missing_components: List[str]
    stale_components: List[str]
    evidence_completeness_pct: int
    evidence_fingerprint: str
