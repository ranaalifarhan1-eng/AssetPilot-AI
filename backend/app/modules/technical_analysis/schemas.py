from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TrendEvidence(BaseModel):
    state: str
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    ema_50: Optional[float] = None
    price_vs_sma_20_pct: Optional[float] = None
    price_vs_sma_50_pct: Optional[float] = None


class MomentumEvidence(BaseModel):
    state: str
    rsi_14: Optional[float] = None
    rsi_state: str = "insufficient_data"
    macd: Optional[float] = None
    signal: Optional[float] = None
    histogram: Optional[float] = None
    macd_state: str = "insufficient_data"
    roc_10_pct: Optional[float] = None


class VolatilityEvidence(BaseModel):
    state: str
    atr_14: Optional[float] = None
    atr_pct: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    bollinger_bandwidth_pct: Optional[float] = None


class StructureEvidence(BaseModel):
    recent_swing_high: Optional[float] = None
    recent_swing_low: Optional[float] = None
    rolling_high_20: Optional[float] = None
    rolling_low_20: Optional[float] = None
    distance_from_high_pct: Optional[float] = None
    distance_from_low_pct: Optional[float] = None


class VolumeEvidence(BaseModel):
    current: Optional[float] = None
    average_20: Optional[float] = None
    relative_volume: Optional[float] = None


class TechnicalAnalysisResponse(BaseModel):
    asset: str
    provider_symbol: str
    timeframe: str
    provider: str
    data_status: str
    source_data_status: str
    candles_used: int
    source_last_updated: Optional[datetime]
    analysis_as_of: Optional[datetime]
    analysis_computed_at: datetime
    current_price: Optional[float] = None
    trend: TrendEvidence
    momentum: MomentumEvidence
    volatility: VolatilityEvidence
    structure: StructureEvidence
    volume: VolumeEvidence


class TimeframeSummary(BaseModel):
    timeframe: str
    data_status: str
    trend_state: str
    momentum_state: str
    volatility_state: str
    rsi_14: Optional[float] = None
    analysis_as_of: Optional[datetime] = None


class MultiTimeframeResponse(BaseModel):
    asset: str
    provider: str = "OKX"
    timeframe_alignment: str
    summaries: Dict[str, TimeframeSummary] = Field(default_factory=dict)
    computed_at: datetime
