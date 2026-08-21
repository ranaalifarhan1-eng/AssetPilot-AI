from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NewsCategory(str, Enum):
    GENERAL = "general"
    CRYPTO = "crypto"
    COMPANY = "company"
    MACRO = "macro"
    REGULATION = "regulation"
    EARNINGS = "earnings"
    TECHNOLOGY = "technology"
    MONETARY_POLICY = "monetary_policy"
    ETF_INSTITUTIONAL = "etf_institutional"

class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"
    UNKNOWN = "unknown"

class ImpactLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"

class NewsDataStatus(str, Enum):
    LIVE = "live"
    CACHED = "cached"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    PROVIDER_NOT_CONFIGURED = "provider_not_configured"

class RelatedAsset(BaseModel):
    symbol: str = Field(..., description="Asset symbol (e.g. BTC, ETH, AAPL, NVDA)")
    display_symbol: str = Field(..., description="Display symbol (e.g. BTC/USDT, AAPL)")
    name: Optional[str] = Field(None, description="Asset display name")
    asset_type: str = Field("crypto", description="'crypto' or 'equity'")
    relationship_type: str = Field("primary", description="'primary', 'secondary', or 'tokenized_exposure'")
    tokenized_symbol: Optional[str] = Field(None, description="Related OKX tokenized symbol if applicable (e.g. xAAPL)")

class NewsArticle(BaseModel):
    id: str = Field(..., description="Deterministic unique identifier for the article")
    external_id: Optional[str] = Field(None, description="Upstream provider external identifier")
    headline: str = Field(..., description="Article title/headline")
    summary: Optional[str] = Field(None, description="Brief provider-supplied excerpt or summary")
    source: str = Field(..., description="Primary ingestion provider (e.g. 'Finnhub', 'SEC RSS', 'Federal Reserve')")
    publisher: Optional[str] = Field(None, description="Publishing outlet or authority (e.g. 'Reuters', 'SEC', 'Bloomberg')")
    url: str = Field(..., description="Canonical source URL")
    published_at: datetime = Field(..., description="Publication timestamp")
    retrieved_at: datetime = Field(..., description="System retrieval timestamp")
    category: NewsCategory = Field(NewsCategory.GENERAL, description="Normalized news category")
    related_assets: List[RelatedAsset] = Field(default_factory=list, description="Mapped related assets")
    related_companies: List[str] = Field(default_factory=list, description="Extracted corporate entities")
    relevance_score: float = Field(0.5, description="Deterministic relevance score [0.0 - 1.0]")
    sentiment_label: SentimentLabel = Field(SentimentLabel.NEUTRAL, description="Conservative sentiment metadata")
    sentiment_score: float = Field(0.0, description="Sentiment score [-1.0 to +1.0]")
    impact_level: ImpactLevel = Field(ImpactLevel.MEDIUM, description="Informational market impact classification")
    is_portfolio_relevant: bool = Field(False, description="True if article directly references a held portfolio asset")
    portfolio_asset_match: Optional[str] = Field(None, description="Held portfolio asset symbol matched")
    duplicate_count: int = Field(1, description="Number of syndicated duplicate stories consolidated")
    data_status: NewsDataStatus = Field(NewsDataStatus.LIVE, description="Machine-readable data provenance")

class NewsListResponse(BaseModel):
    articles: List[NewsArticle] = Field(default_factory=list, description="List of normalized news articles")
    total_count: int = Field(0, description="Total matching articles")
    portfolio_relevant_count: int = Field(0, description="Number of articles matching held portfolio assets")
    last_collected_at: Optional[datetime] = Field(None, description="Timestamp of latest collection run")
    data_status: NewsDataStatus = Field(NewsDataStatus.LIVE, description="Overall collection state")

class NewsStatusResponse(BaseModel):
    configured_sources: List[str] = Field(default_factory=list, description="Configured provider names")
    active_sources: List[str] = Field(default_factory=list, description="Currently responsive provider names")
    total_cached_articles: int = Field(0, description="Total articles currently held in in-memory store")
    last_successful_collection: Optional[datetime] = Field(None, description="Timestamp of last collection")
    provider_statuses: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Status breakdown per provider")
