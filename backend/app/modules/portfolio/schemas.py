from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class AccountSourceBalance(BaseModel):
    source: str = Field(..., description="Account source name, e.g., 'Trading' or 'Funding'")
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
    estimated_value_usdt: Optional[str] = Field(None, description="Estimated total value in USDT")
    valuation_available: bool = Field(True, description="Whether market valuation is available")
    allocation_pct: float = Field(0.0, description="Percentage share of total portfolio value")

class PortfolioSummary(BaseModel):
    total_value_usdt: str = Field("0.00", description="Total portfolio value in USDT")
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
    connection_status: str = Field(..., description="Status: 'connected', 'unconfigured', 'error'")

class AccountSourcesResponse(BaseModel):
    provider: str = "OKX"
    sources: List[str] = ["Trading", "Funding"]
    configured: bool
