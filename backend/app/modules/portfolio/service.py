import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from app.modules.portfolio.okx_account import OKXAccountClient
from app.modules.portfolio.schemas import (
    PortfolioSummary,
    PortfolioAsset,
    AccountSourceBalance,
    PortfolioStatusResponse,
)
from app.modules.market_data.service import MarketDataService
from app.modules.market_data.cache import global_cache

logger = logging.getLogger(__name__)

# Map asset names
ASSET_NAMES: Dict[str, str] = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "USDT": "Tether",
    "USDC": "USD Coin",
    "WIF": "dogwifhat",
    "ETHW": "EthereumPoW",
    "OKB": "OKB Token",
    "FIL": "Filecoin",
}

def parse_decimal(val: Any, default: str = "0") -> Decimal:
    if not val:
        return Decimal(default)
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)

class PortfolioService:
    def __init__(self, account_client: Optional[OKXAccountClient] = None, market_service: Optional[MarketDataService] = None):
        self.account_client = account_client or OKXAccountClient()
        self.market_service = market_service or MarketDataService()

    def get_status(self) -> PortfolioStatusResponse:
        is_config = self.account_client.is_configured()
        return PortfolioStatusResponse(
            configured=is_config,
            provider="OKX",
            read_only_expected=True,
            last_successful_sync=datetime.now(timezone.utc) if is_config else None,
            connection_status="connected" if is_config else "unconfigured"
        )

    async def get_portfolio_summary(self) -> PortfolioSummary:
        if not self.account_client.is_configured():
            return PortfolioSummary(
                total_value_usdt="0.00",
                assets=[],
                asset_count=0,
                last_synced_at=None,
                provider="OKX",
                data_status="unconfigured",
                error_message="OKX read-only API credentials not configured in backend environment."
            )

        cache_key = "portfolio_summary"
        cached = await global_cache.get(cache_key)
        if cached:
            return cached

        try:
            trading_raw = await self.account_client.fetch_trading_balances()
            funding_raw = await self.account_client.fetch_funding_balances()

            merged: Dict[str, Dict] = {}
            for item in trading_raw + funding_raw:
                sym = item["currency"].upper()
                if sym not in merged:
                    merged[sym] = {
                        "symbol": sym,
                        "name": ASSET_NAMES.get(sym, sym),
                        "total_balance": Decimal("0"),
                        "available_balance": Decimal("0"),
                        "frozen_balance": Decimal("0"),
                        "account_sources": []
                    }

                bal_dec = parse_decimal(item.get("balance"))
                avail_dec = parse_decimal(item.get("available"))
                froz_dec = parse_decimal(item.get("frozen"))

                merged[sym]["total_balance"] += bal_dec
                merged[sym]["available_balance"] += avail_dec
                merged[sym]["frozen_balance"] += froz_dec
                merged[sym]["account_sources"].append(
                    AccountSourceBalance(
                        source=item["source"],
                        balance=str(bal_dec),
                        available=str(avail_dec),
                        frozen=str(froz_dec)
                    )
                )

            # Value portfolio assets using market data
            portfolio_assets: List[PortfolioAsset] = []
            total_portfolio_usdt = Decimal("0")

            for sym, asset_data in merged.items():
                price_usdt_dec: Optional[Decimal] = None
                valuation_available = True

                if sym in ["USDT", "USD"]:
                    price_usdt_dec = Decimal("1.0")
                else:
                    try:
                        ticker = await self.market_service.get_ticker(sym)
                        price_usdt_dec = parse_decimal(ticker.price, default="0")
                    except Exception:
                        price_usdt_dec = None
                        valuation_available = False

                est_val_usdt_dec: Optional[Decimal] = None
                if price_usdt_dec is not None:
                    est_val_usdt_dec = asset_data["total_balance"] * price_usdt_dec
                    total_portfolio_usdt += est_val_usdt_dec

                portfolio_assets.append(
                    PortfolioAsset(
                        symbol=sym,
                        name=asset_data["name"],
                        total_balance=f"{asset_data['total_balance']:.8f}".rstrip('0').rstrip('.'),
                        available_balance=f"{asset_data['available_balance']:.8f}".rstrip('0').rstrip('.'),
                        frozen_balance=f"{asset_data['frozen_balance']:.8f}".rstrip('0').rstrip('.'),
                        account_sources=asset_data["account_sources"],
                        price_usdt=str(price_usdt_dec) if price_usdt_dec is not None else None,
                        estimated_value_usdt=f"{est_val_usdt_dec:.2f}" if est_val_usdt_dec is not None else None,
                        valuation_available=valuation_available,
                        allocation_pct=0.0
                    )
                )

            # Compute allocation percentages
            if total_portfolio_usdt > 0:
                for asset in portfolio_assets:
                    if asset.estimated_value_usdt is not None:
                        val_dec = parse_decimal(asset.estimated_value_usdt)
                        asset.allocation_pct = round(float((val_dec / total_portfolio_usdt) * Decimal("100")), 2)

            # Sort by estimated value descending
            portfolio_assets.sort(
                key=lambda a: float(a.estimated_value_usdt or "0"),
                reverse=True
            )

            summary = PortfolioSummary(
                total_value_usdt=f"{total_portfolio_usdt:.2f}",
                assets=portfolio_assets,
                asset_count=len(portfolio_assets),
                last_synced_at=datetime.now(timezone.utc),
                provider="OKX",
                data_status="configured",
                error_message=None
            )

            await global_cache.set(cache_key, summary, ttl=15.0)
            return summary

        except Exception as e:
            logger.error(f"Error fetching portfolio summary: {e}")
            return PortfolioSummary(
                total_value_usdt="0.00",
                assets=[],
                asset_count=0,
                last_synced_at=None,
                provider="OKX",
                data_status="error",
                error_message=f"Failed to sync OKX portfolio: {str(e)}"
            )
