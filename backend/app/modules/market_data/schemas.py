from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class AssetInfo(BaseModel):
    symbol: str = Field(..., description="Normalized symbol, e.g., BTC")
    name: str = Field(..., description="Full asset name, e.g., Bitcoin")
    category: str = Field("Crypto", description="Asset class/category")
    provider_symbol: str = Field(..., description="Provider instrument ID, e.g., BTC-USDT")

class NormalizedTicker(BaseModel):
    symbol: str = Field(..., description="Normalized internal symbol (e.g. BTC)")
    provider_symbol: str = Field(..., description="Provider instrument ID (e.g. BTC-USDT)")
    name: str = Field(..., description="Asset display name")
    price: str = Field(..., description="Current price string formatted safely")
    open_24h: str = Field(..., description="24h open price")
    high_24h: str = Field(..., description="24h high price")
    low_24h: str = Field(..., description="24h low price")
    volume_24h: str = Field(..., description="24h base asset volume")
    quote_volume_24h: str = Field(..., description="24h quote asset volume")
    change_24h_abs: str = Field(..., description="Absolute 24h price change")
    change_24h_pct: float = Field(..., description="Percentage 24h price change")
    timestamp: datetime = Field(..., description="Data timestamp")
    provider: str = Field("OKX", description="Data provider name")

class NormalizedCandle(BaseModel):
    timestamp: datetime = Field(..., description="Candle open timestamp")
    open: str = Field(..., description="Open price")
    high: str = Field(..., description="High price")
    low: str = Field(..., description="Low price")
    close: str = Field(..., description="Close price")
    volume: str = Field(..., description="Base volume")

class CandleResponse(BaseModel):
    symbol: str
    timeframe: str
    provider: str
    candles: List[NormalizedCandle]

class MarketOverviewResponse(BaseModel):
    updated_at: datetime
    provider: str
    tickers: List[NormalizedTicker]
