from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum

class AssetCategory(str, Enum):
    CRYPTO = "crypto"
    EQUITY = "equity"
    TOKENIZED_EQUITY = "tokenized_equity"
    ETF = "etf"
    INDEX_REFERENCE = "index_reference"

class DataStatus(str, Enum):
    LIVE = "live"
    CACHED = "cached"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    PROVIDER_NOT_CONFIGURED = "provider_not_configured"

class AssetInfo(BaseModel):
    symbol: str = Field(..., description="Normalized symbol, e.g., BTC, GOOGL, xGOOGL")
    name: str = Field(..., description="Full asset or company name")
    category: str = Field("crypto", description="Asset category: crypto, equity, tokenized_equity, etf, index_reference")
    provider_symbol: str = Field(..., description="Provider instrument ID, e.g., BTC-USDT, GOOGL, XGOOGL-USDT")
    internal_id: Optional[str] = Field(None, description="Unique internal asset ID")
    display_symbol: Optional[str] = Field(None, description="Display formatted symbol, e.g., BTC/USDT, GOOGL, xGOOGL/USDT")
    provider: str = Field("OKX", description="Primary data provider name")
    quote_currency: str = Field("USDT", description="Quote/base currency, e.g. USDT, USD")
    underlying_symbol: Optional[str] = Field(None, description="Underlying equity symbol if tokenized, e.g. GOOGL")
    underlying_name: Optional[str] = Field(None, description="Underlying company name if tokenized")
    venue: str = Field("OKX SPOT", description="Execution or reference venue, e.g. NASDAQ, NYSE, OKX SPOT")
    market_status: str = Field("24/7", description="Market availability state, e.g. open, closed, 24/7")
    tradable_on_provider: bool = Field(True, description="Whether tradable on the provider platform")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional provider/instrument metadata")

    def model_post_init(self, __context: Any) -> None:
        if not self.internal_id:
            self.internal_id = f"{self.category}:{self.symbol.lower()}"
        if not self.display_symbol:
            if self.category == "crypto":
                self.display_symbol = f"{self.symbol}/USDT"
            elif self.category == "tokenized_equity":
                self.display_symbol = f"{self.symbol}/USDT"
            else:
                self.display_symbol = self.symbol

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
    data_status: str = Field("live", description="Provenance status: live, cached, stale, unavailable")

class NormalizedEquityQuote(BaseModel):
    symbol: str = Field(..., description="Equity ticker symbol (e.g. AAPL, GOOGL)")
    name: str = Field(..., description="Company name")
    asset_type: str = Field("equity", description="Asset type discriminator")
    provider: str = Field("Finnhub", description="Data provider source")
    price: Optional[str] = Field(None, description="Current/latest market price, null if unconfigured")
    previous_close: Optional[str] = Field(None, description="Previous session close price")
    open_price: Optional[str] = Field(None, description="Current session open price")
    high: Optional[str] = Field(None, description="Day high price")
    low: Optional[str] = Field(None, description="Day low price")
    change_abs: Optional[str] = Field(None, description="Day price change absolute")
    change_pct: Optional[float] = Field(None, description="Day price change percentage")
    volume: Optional[str] = Field(None, description="Trading volume")
    currency: str = Field("USD", description="Quoted currency")
    market_timestamp: Optional[datetime] = Field(None, description="Quote timestamp from provider")
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Local fetch timestamp")
    market_state: str = Field("closed", description="Market status: open, closed")
    data_status: str = Field("live", description="Provenance status: live, cached, stale, unavailable, provider_not_configured")

class NormalizedTokenizedEquityQuote(BaseModel):
    symbol: str = Field(..., description="Token symbol (e.g. xGOOGL)")
    display_symbol: str = Field(..., description="Display symbol (e.g. xGOOGL/USDT)")
    name: str = Field(..., description="Instrument display name")
    asset_type: str = Field("tokenized_equity", description="Asset type discriminator")
    provider: str = Field("OKX", description="Data provider source")
    provider_symbol: str = Field(..., description="OKX instrument ID (e.g. XGOOGL-USDT)")
    underlying_symbol: str = Field(..., description="Underlying equity symbol (e.g. GOOGL)")
    underlying_name: str = Field(..., description="Underlying company name")
    price: Optional[str] = Field(None, description="Current OKX token price in USDT")
    open_24h: Optional[str] = Field(None, description="24h open price")
    high_24h: Optional[str] = Field(None, description="24h high price")
    low_24h: Optional[str] = Field(None, description="24h low price")
    volume_24h: Optional[str] = Field(None, description="24h base token volume")
    quote_volume_24h: Optional[str] = Field(None, description="24h quote volume (USDT)")
    change_24h_abs: Optional[str] = Field(None, description="24h price change absolute")
    change_24h_pct: Optional[float] = Field(None, description="24h price change percentage")
    quote_currency: str = Field("USDT", description="Quote currency")
    tokenized_label: str = Field("Tokenized Equity • OKX", description="Explicit tokenized designation")
    timestamp: Optional[datetime] = Field(None, description="OKX timestamp")
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Local fetch timestamp")
    data_status: str = Field("live", description="Provenance status: live, cached, stale, unavailable")

class EquityComparisonResponse(BaseModel):
    underlying_symbol: str = Field(..., description="Underlying equity ticker, e.g. GOOGL")
    underlying_name: str = Field(..., description="Underlying company name")
    comparison_available: bool = Field(..., description="Whether both underlying and tokenized live quotes are available")
    unavailability_reason: Optional[str] = Field(None, description="Reason comparison cannot be calculated")
    underlying_price: Optional[str] = Field(None, description="Traditional reference price in USD")
    underlying_provider: str = Field("Finnhub", description="Traditional equity source")
    underlying_data_status: str = Field("provider_not_configured", description="Underlying data provenance")
    underlying_market_state: str = Field("closed", description="Traditional market state: open, closed")
    underlying_timestamp: Optional[datetime] = Field(None, description="Traditional quote timestamp")
    tokenized_counterpart_available: bool = Field(..., description="Whether an OKX tokenized counterpart is listed")
    tokenized_symbol: Optional[str] = Field(None, description="Tokenized symbol, e.g. xGOOGL")
    tokenized_provider: Optional[str] = Field(None, description="Tokenized venue, e.g. OKX")
    tokenized_data_status: Optional[str] = Field(None, description="Tokenized quote provenance")
    tokenized_price: Optional[str] = Field(None, description="OKX tokenized price in USDT")
    tokenized_timestamp: Optional[datetime] = Field(None, description="OKX token timestamp")
    price_difference_abs: Optional[str] = Field(None, description="Reference absolute difference")
    price_difference_pct: Optional[float] = Field(None, description="Reference percentage difference")
    comparison_label: str = Field("Reference Price Difference", description="Standardized label (never arbitrage)")
    disclaimer: str = Field(
        "Prices may differ due to market hours, liquidity, venue structure, and update timing. Not an arbitrage signal.",
        description="Mandatory compliance disclaimer"
    )

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
    data_status: str = Field("live", description="Response provenance: live or cached")

class MarketOverviewResponse(BaseModel):
    updated_at: datetime
    provider: str
    tickers: List[NormalizedTicker]
    data_status: str = Field("live", description="Response provenance: live or cached")
