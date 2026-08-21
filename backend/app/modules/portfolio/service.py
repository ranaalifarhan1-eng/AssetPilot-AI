import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
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

CACHE_PREFIX_LAST_PRICE = "last_known_price:"
STALE_PRICE_MAX_AGE_SECONDS = 900.0  # 15 minutes staleness window for fallback pricing

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
            last_successful_sync=None,
            connection_status="configured_unverified" if is_config else "unconfigured"
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
                stale_assets=[],
                stale_window_seconds=int(STALE_PRICE_MAX_AGE_SECONDS),
                last_complete_valuation_at=None,
                last_complete_total_usdt=None,
                assets=[],
                asset_count=0,
                last_synced_at=None,
                provider="OKX",
                data_status="unconfigured",
                error_message="OKX read-only API credentials not configured in backend environment."
            )

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

            now = datetime.now(timezone.utc)

            # Concurrently resolve prices with price provenance & safe staleness fallback
            async def resolve_asset_price(sym: str) -> Tuple[str, Optional[Decimal], str, Optional[datetime]]:
                """
                Returns (symbol, price_decimal, price_status, price_as_of).
                price_status: 'live', 'cached', 'stale', 'unavailable'
                """
                # 1. Base quote currency identity
                if sym in ["USDT", "USD"]:
                    one_dec = Decimal("1.0")
                    await global_cache.set(f"{CACHE_PREFIX_LAST_PRICE}{sym}", {"price": one_dec, "as_of": now}, ttl=3600.0)
                    return sym, one_dec, "live", now

                # 2. Attempt live price resolution from market provider
                try:
                    ticker = await self.market_service.get_ticker(sym)
                    p_dec = parse_decimal(ticker.price, default="0")
                    if p_dec > Decimal("0"):
                        # Save as last-known-good price in cache (1 hour retention)
                        await global_cache.set(f"{CACHE_PREFIX_LAST_PRICE}{sym}", {"price": p_dec, "as_of": now}, ttl=3600.0)
                        return sym, p_dec, "live", now
                except Exception as e:
                    logger.debug(f"Live ticker lookup failed for {sym}: {e}")

                # 3. If live lookup failed, check last-known-good price cache
                cached_price_entry = await global_cache.get(f"{CACHE_PREFIX_LAST_PRICE}{sym}")
                if cached_price_entry and isinstance(cached_price_entry, dict):
                    cached_p = cached_price_entry.get("price")
                    cached_as_of = cached_price_entry.get("as_of")
                    if cached_p and cached_as_of:
                        as_of_utc = cached_as_of if cached_as_of.tzinfo else cached_as_of.replace(tzinfo=timezone.utc)
                        age_sec = (now - as_of_utc).total_seconds()
                        if age_sec <= STALE_PRICE_MAX_AGE_SECONDS:
                            logger.info(f"Using eligible last-known-good price for {sym} (age: {age_sec:.1f}s <= {STALE_PRICE_MAX_AGE_SECONDS}s)")
                            return sym, parse_decimal(cached_p), "stale", as_of_utc

                # 4. Price unavailable / expired
                return sym, None, "unavailable", None

            price_tasks = [resolve_asset_price(sym) for sym in non_zero_assets.keys()]
            price_results = await asyncio.gather(*price_tasks, return_exceptions=True)

            prices_map: Dict[str, Tuple[Optional[Decimal], str, Optional[datetime]]] = {}
            for res in price_results:
                if isinstance(res, tuple) and len(res) == 4:
                    sym, p_dec, p_status, p_as_of = res
                    prices_map[sym] = (p_dec, p_status, p_as_of)

            portfolio_assets: List[PortfolioAsset] = []
            total_portfolio_usdt = Decimal("0")
            unvalued_symbols: List[str] = []
            stale_symbols: List[str] = []
            valued_count = 0

            for sym, asset_data in non_zero_assets.items():
                price_usdt_dec, price_status, price_as_of = prices_map.get(sym, (None, "unavailable", None))

                est_val_usdt_dec: Optional[Decimal] = None
                valuation_available = False

                if price_usdt_dec is not None and price_status in ["live", "cached", "stale"]:
                    # CRITICAL: Dynamically compute value using current balance * price
                    est_val_usdt_dec = asset_data["total_balance"] * price_usdt_dec
                    total_portfolio_usdt += est_val_usdt_dec
                    valuation_available = True
                    valued_count += 1
                    if price_status == "stale":
                        stale_symbols.append(sym)
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
                        price_status=price_status,
                        price_as_of=price_as_of,
                        estimated_value_usdt=f"{est_val_usdt_dec:.2f}" if est_val_usdt_dec is not None else None,
                        valuation_available=valuation_available,
                        allocation_pct=0.0
                    )
                )

            # Compute dynamic allocation percentages
            if total_portfolio_usdt > Decimal("0"):
                for asset in portfolio_assets:
                    if asset.estimated_value_usdt is not None:
                        val_dec = parse_decimal(asset.estimated_value_usdt)
                        asset.allocation_pct = round(float((val_dec / total_portfolio_usdt) * Decimal("100")), 2)

            # Sort by estimated value descending (priced first, then by total balance)
            portfolio_assets.sort(
                key=lambda a: (
                    float(a.estimated_value_usdt or "0"),
                    float(a.total_balance or "0")
                ),
                reverse=True
            )

            # Valuation Completeness Evaluation
            if len(unvalued_symbols) == 0 and len(stale_symbols) == 0:
                # 100% Live Complete Valuation
                valuation_status = "complete"
                valuation_complete = True
                total_value_str = f"{total_portfolio_usdt:.2f}"
                last_complete_time = now
                last_complete_total = total_value_str
            elif len(unvalued_symbols) == 0 and len(stale_symbols) > 0:
                # All assets priced, but one or more use eligible stale prices
                valuation_status = "stale_complete"
                valuation_complete = False
                total_value_str = f"{total_portfolio_usdt:.2f}"  # Dynamically computed with new current balances!
                # Timestamp is the oldest stale price timestamp
                stale_times = [a.price_as_of for a in portfolio_assets if a.price_status == "stale" and a.price_as_of]
                last_complete_time = min(stale_times) if stale_times else now
                last_complete_total = total_value_str
            else:
                # One or more assets cannot be priced
                valuation_status = "partial"
                valuation_complete = False
                total_value_str = f"{total_portfolio_usdt:.2f}"
                last_complete_time = None
                last_complete_total = None

            summary = PortfolioSummary(
                total_value_usdt=total_value_str,
                known_value_usdt=f"{total_portfolio_usdt:.2f}",
                valuation_status=valuation_status,
                valuation_complete=valuation_complete,
                valued_asset_count=valued_count,
                unvalued_asset_count=len(unvalued_symbols),
                unvalued_assets=unvalued_symbols,
                stale_assets=stale_symbols,
                stale_window_seconds=int(STALE_PRICE_MAX_AGE_SECONDS),
                last_complete_valuation_at=last_complete_time,
                last_complete_total_usdt=last_complete_total,
                assets=portfolio_assets,
                asset_count=len(portfolio_assets),
                last_synced_at=now,
                provider="OKX",
                data_status="configured",
                error_message=None
            )

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
                stale_assets=[],
                stale_window_seconds=int(STALE_PRICE_MAX_AGE_SECONDS),
                last_complete_valuation_at=None,
                last_complete_total_usdt=None,
                assets=[],
                asset_count=0,
                last_synced_at=None,
                provider="OKX",
                data_status="error",
                error_message="Failed to sync OKX portfolio. Verify the read-only connection and try again."
            )
