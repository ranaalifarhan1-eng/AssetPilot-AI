import logging
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from app.modules.portfolio.okx_account import OKXAccountClient
from app.modules.portfolio.schemas import (
    PortfolioSummary,
    PortfolioAsset,
    AccountSourceBalance,
    PortfolioStatusResponse,
    RawAccountBalance,
)
from app.modules.market_data.service import MarketDataService
from app.modules.market_data.cache import global_cache

logger = logging.getLogger(__name__)

CACHE_KEY_LATEST = "portfolio_summary"
CACHE_KEY_LAST_COMPLETE = "portfolio_summary_last_complete"

# Map asset names
ASSET_NAMES: Dict[str, str] = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "USDT": "Tether",
    "USDC": "USD Coin",
    "USDG": "USD Global",
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
        is_config = self.account_client.is_configured() if callable(self.account_client.is_configured) else bool(self.account_client.is_configured)
        return PortfolioStatusResponse(
            configured=is_config,
            provider="OKX",
            read_only_expected=True,
            last_successful_sync=datetime.now(timezone.utc) if is_config else None,
            connection_status="connected" if is_config else "unconfigured"
        )

    async def get_portfolio_summary(self) -> PortfolioSummary:
        is_config = self.account_client.is_configured() if callable(self.account_client.is_configured) else bool(self.account_client.is_configured)
        if not is_config:
            return PortfolioSummary(
                total_value_usdt="0.00",
                known_value_usdt="0.00",
                valuation_status="unconfigured",
                valuation_complete=False,
                valued_asset_count=0,
                unvalued_asset_count=0,
                unvalued_assets=[],
                last_complete_valuation_at=None,
                last_complete_total_usdt=None,
                assets=[],
                asset_count=0,
                last_synced_at=None,
                provider="OKX",
                data_status="unconfigured",
                error_message="OKX read-only API credentials not configured in backend environment."
            )

        cached = await global_cache.get(CACHE_KEY_LATEST)
        if cached:
            return cached

        try:
            # Concurrently fetch Trading, Funding, and Earn balances
            trading_raw, funding_raw, earn_raw = await asyncio.gather(
                self.account_client.fetch_trading_balances(),
                self.account_client.fetch_funding_balances(),
                self.account_client.fetch_earn_balances(),
                return_exceptions=False
            )

            all_raw = trading_raw + funding_raw + earn_raw
            merged: Dict[str, Dict] = {}

            for item in all_raw:
                if isinstance(item, RawAccountBalance):
                    sym = item.ccy.upper()
                    bal_val = item.total
                    avail_val = item.available
                    froz_val = item.frozen
                    src_val = item.source
                elif isinstance(item, dict):
                    sym = (item.get("ccy") or item.get("currency", "")).upper()
                    bal_val = item.get("balance") or item.get("total", "0")
                    avail_val = item.get("available", "0")
                    froz_val = item.get("frozen", "0")
                    src_val = item.get("source", "Unknown")
                else:
                    continue

                if not sym:
                    continue

                if sym not in merged:
                    merged[sym] = {
                        "symbol": sym,
                        "name": ASSET_NAMES.get(sym, sym),
                        "total_balance": Decimal("0"),
                        "available_balance": Decimal("0"),
                        "frozen_balance": Decimal("0"),
                        "account_sources": []
                    }

                bal_dec = parse_decimal(bal_val)
                avail_dec = parse_decimal(avail_val)
                froz_dec = parse_decimal(froz_val)

                merged[sym]["total_balance"] += bal_dec
                merged[sym]["available_balance"] += avail_dec
                merged[sym]["frozen_balance"] += froz_dec
                merged[sym]["account_sources"].append(
                    AccountSourceBalance(
                        source=src_val,
                        balance=str(bal_dec),
                        available=str(avail_dec),
                        frozen=str(froz_dec)
                    )
                )

            # Filter out zero balance dust
            non_zero_assets = {
                sym: data for sym, data in merged.items()
                if data["total_balance"] > Decimal("0")
            }

            # Concurrently resolve prices for held assets
            async def resolve_price(sym: str) -> tuple[str, Optional[Decimal], bool]:
                if sym in ["USDT", "USD"]:
                    return sym, Decimal("1.0"), True
                try:
                    ticker = await self.market_service.get_ticker(sym)
                    p_dec = parse_decimal(ticker.price, default="0")
                    if p_dec > Decimal("0"):
                        return sym, p_dec, True
                    return sym, None, False
                except Exception:
                    return sym, None, False

            price_tasks = [resolve_price(sym) for sym in non_zero_assets.keys()]
            price_results = await asyncio.gather(*price_tasks, return_exceptions=True)

            prices_map: Dict[str, tuple[Optional[Decimal], bool]] = {}
            for res in price_results:
                if isinstance(res, tuple) and len(res) == 3:
                    sym, p_dec, avail = res
                    prices_map[sym] = (p_dec, avail)

            portfolio_assets: List[PortfolioAsset] = []
            known_value_dec = Decimal("0")
            unvalued_symbols: List[str] = []
            valued_count = 0

            for sym, asset_data in non_zero_assets.items():
                price_usdt_dec, valuation_available = prices_map.get(sym, (None, False))

                est_val_usdt_dec: Optional[Decimal] = None
                if valuation_available and price_usdt_dec is not None:
                    est_val_usdt_dec = asset_data["total_balance"] * price_usdt_dec
                    known_value_dec += est_val_usdt_dec
                    valued_count += 1
                else:
                    unvalued_symbols.append(sym)

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

            # Compute allocation percentages based on known value
            if known_value_dec > Decimal("0"):
                for asset in portfolio_assets:
                    if asset.estimated_value_usdt is not None:
                        val_dec = parse_decimal(asset.estimated_value_usdt)
                        asset.allocation_pct = round(float((val_dec / known_value_dec) * Decimal("100")), 2)

            # Sort by estimated value descending (priced first, then by total balance)
            portfolio_assets.sort(
                key=lambda a: (
                    float(a.estimated_value_usdt or "0"),
                    float(a.total_balance or "0")
                ),
                reverse=True
            )

            now = datetime.now(timezone.utc)
            last_complete_snapshot: Optional[PortfolioSummary] = await global_cache.get(CACHE_KEY_LAST_COMPLETE)

            # Valuation completeness determination
            if len(unvalued_symbols) == 0:
                # Complete Valuation
                valuation_status = "complete"
                valuation_complete = True
                total_value_str = f"{known_value_dec:.2f}"
                last_complete_time = now
                last_complete_total = total_value_str
            else:
                valuation_complete = False
                if last_complete_snapshot and last_complete_snapshot.valuation_complete:
                    # Stale Complete Fallback
                    valuation_status = "stale_complete"
                    total_value_str = last_complete_snapshot.total_value_usdt
                    last_complete_time = last_complete_snapshot.last_synced_at
                    last_complete_total = last_complete_snapshot.total_value_usdt
                else:
                    # Partial Valuation
                    valuation_status = "partial"
                    total_value_str = f"{known_value_dec:.2f}"
                    last_complete_time = None
                    last_complete_total = None

            summary = PortfolioSummary(
                total_value_usdt=total_value_str,
                known_value_usdt=f"{known_value_dec:.2f}",
                valuation_status=valuation_status,
                valuation_complete=valuation_complete,
                valued_asset_count=valued_count,
                unvalued_asset_count=len(unvalued_symbols),
                unvalued_assets=unvalued_symbols,
                last_complete_valuation_at=last_complete_time,
                last_complete_total_usdt=last_complete_total,
                assets=portfolio_assets,
                asset_count=len(portfolio_assets),
                last_synced_at=now,
                provider="OKX",
                data_status="configured",
                error_message=None
            )

            # Save complete snapshot separately if complete
            if valuation_complete:
                await global_cache.set(CACHE_KEY_LAST_COMPLETE, summary, ttl=3600.0)

            # Cache latest portfolio summary for 30 seconds
            await global_cache.set(CACHE_KEY_LATEST, summary, ttl=30.0)
            return summary

        except Exception as e:
            logger.error(f"Error fetching portfolio summary: {e}")
            return PortfolioSummary(
                total_value_usdt="0.00",
                known_value_usdt="0.00",
                valuation_status="error",
                valuation_complete=False,
                valued_asset_count=0,
                unvalued_asset_count=0,
                unvalued_assets=[],
                last_complete_valuation_at=None,
                last_complete_total_usdt=None,
                assets=[],
                asset_count=0,
                last_synced_at=None,
                provider="OKX",
                data_status="error",
                error_message=f"Failed to sync OKX portfolio: {str(e)}"
            )
