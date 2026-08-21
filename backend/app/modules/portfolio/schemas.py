from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class RawAccountBalance(BaseModel):
    ccy: str
    total: str
    available: str
    frozen: str = "0"
    source: str

class AccountSourceBalance(BaseModel):
    source: str = Field(..., description="Account source name, e.g., 'Trading', 'Funding', 'Earn'")
    balance: str = Field(..., description="Total balance in this account source")
    available: str = Field(..., description="Available balance")
    frozen: str = Field("0", description="Frozen/locked balance")

class PortfolioAsset(BaseModel):
    symbol: str = Field(..., description="Normalized asset symbol (e.g. BTC, ETH, USDT)")
    name: str = Field(..., description="Asset display name")
    total_balance: str = Field(..., description="Total aggregated balance across account sources")
    available_balance: str = Field(..., description="Total available balance across account sources")
    frozen_balance: str = Field("0", description="Total frozen balance across account sources")
    account_sources: List[AccountSourceBalance] = Field(default_factory=list, description="Breakdown by account type")
    price_usdt: Optional[str] = Field(None, description="Current price in USDT from market provider")
    price_status: str = Field("live", description="Price provenance: 'live', 'cached', 'stale', 'unavailable'")
    price_as_of: Optional[datetime] = Field(None, description="Timestamp when market price was observed")
    estimated_value_usdt: Optional[str] = Field(None, description="Estimated total value in USDT")
    valuation_available: bool = Field(True, description="Whether market valuation is available")
    allocation_pct: float = Field(0.0, description="Percentage share of total portfolio value")

class PortfolioSummary(BaseModel):
    total_value_usdt: str = Field("0.00", description="Total portfolio value in USDT calculated from current balances")
    known_value_usdt: str = Field("0.00", description="Sum of currently priced assets in USDT")
    valuation_status: str = Field("unconfigured", description="Status: 'complete', 'partial', 'stale_complete', 'unavailable', 'unconfigured', 'error'")
    valuation_complete: bool = Field(False, description="Whether all held non-zero assets are priced with live data")
    valued_asset_count: int = Field(0, description="Number of assets with resolved market prices")
    unvalued_asset_count: int = Field(0, description="Number of assets lacking market prices")
    unvalued_assets: List[str] = Field(default_factory=list, description="Symbols of held assets lacking market prices")
    stale_assets: List[str] = Field(default_factory=list, description="Symbols of held assets valued using stale prices")
    stale_window_seconds: int = Field(900, description="Maximum staleness window in seconds for fallback pricing")
    last_complete_valuation_at: Optional[datetime] = Field(None, description="Timestamp of the last fully complete valuation")
    last_complete_total_usdt: Optional[str] = Field(None, description="Total value recorded in the last fully complete valuation")
    assets: List[PortfolioAsset] = Field(default_factory=list, description="List of held portfolio assets")
    asset_count: int = Field(0, description="Number of held assets with non-zero balances")
    last_synced_at: Optional[datetime] = Field(None, description="Timestamp of last portfolio sync")
    provider: str = Field("OKX", description="Portfolio data provider")
    data_status: str = Field("unconfigured", description="Data status: 'configured', 'unconfigured', 'error'")
    error_message: Optional[str] = Field(None, description="Safe error message if sync failed")

class PortfolioStatusResponse(BaseModel):
    configured: bool = Field(..., description="Whether OKX read-only API credentials are configured in backend")
    provider: str = Field("OKX", description="Portfolio data provider")
    read_only_expected: bool = Field(True, description="Enforces strict read-only requirement")
    last_successful_sync: Optional[datetime] = Field(None, description="Timestamp of last successful sync")
    connection_status: str = Field(..., description="Status: 'configured_unverified', 'unconfigured', 'error'")

class AccountSourcesResponse(BaseModel):
    provider: str = "OKX"
    sources: List[str] = ["Trading", "Funding", "Earn"]
    configured: bool
