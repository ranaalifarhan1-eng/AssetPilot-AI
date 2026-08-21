import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from app.modules.macro.schemas import (
    EconomicEvent,
    YieldCurveData,
    MacroStatusResponse,
)
from app.modules.macro.providers.base import BaseMacroProvider
from app.modules.macro.providers.fed_provider import FederalReserveProvider
from app.modules.macro.providers.treasury_provider import TreasuryProvider
from app.modules.macro.providers.official_schedule_provider import OfficialScheduleProvider
from app.modules.macro.providers.fred_provider import FREDProvider
from app.modules.market_data.cache import global_cache

logger = logging.getLogger(__name__)

CACHE_KEY_EVENTS = "macro_events_all"
CACHE_KEY_YIELD_CURVE = "macro_yield_curve"
CACHE_KEY_STATUS = "macro_status"

EVENTS_CACHE_TTL = 1800.0  # 30 minutes
YIELD_CURVE_TTL = 3600.0   # 1 hour

class MacroService:
    """
    Orchestrates macroeconomic intelligence:
    - Multi-provider collection (Federal Reserve, U.S. Treasury, BLS/BEA/Census, FRED)
    - Deduplication & normalization
    - Deterministic surprise & context derivation
    - Cached portfolio exposure mapping without extra authenticated exchange requests
    """

    def __init__(self, providers: Optional[List[BaseMacroProvider]] = None):
        self.providers = providers or [
            FederalReserveProvider(),
            TreasuryProvider(),
            OfficialScheduleProvider(),
            FREDProvider(),
        ]
        self._treasury_provider = next((p for p in self.providers if isinstance(p, TreasuryProvider)), TreasuryProvider())

    async def get_status(self) -> MacroStatusResponse:
        events = await self.get_all_events()
        yield_curve = await self.get_yield_curve()
        now_utc = datetime.now(timezone.utc)

        upcoming_count = sum(1 for e in events if e.event_status == "upcoming")
        recent_count = sum(1 for e in events if e.event_status in ["released", "revised"])
        configured_providers = [p.provider_name for p in self.providers if p.is_configured()]

        return MacroStatusResponse(
            service="Macro & Economic Events Intelligence",
            status="ok",
            providers_configured=configured_providers,
            total_events_tracked=len(events),
            upcoming_events_count=upcoming_count,
            recent_events_count=recent_count,
            last_collection_at=now_utc,
            yield_curve_date=yield_curve.date if yield_curve else None
        )

    async def _get_held_symbols(self) -> List[str]:
        """Reads user's currently held symbols from the portfolio cache safely."""
        try:
            cached_portfolio = await global_cache.get("portfolio_summary")
            if cached_portfolio and hasattr(cached_portfolio, "assets"):
                return [a.symbol for a in cached_portfolio.assets if float(a.total_balance or "0") > 0]
        except Exception as e:
            logger.debug(f"Failed to read portfolio cache for macro exposure: {e}")
        return []

    async def fetch_and_normalize_all(self, force: bool = False) -> List[EconomicEvent]:
        """Fetches from all configured providers, deduplicates, and caches."""
        if not force:
            cached_events: Optional[List[EconomicEvent]] = await global_cache.get(CACHE_KEY_EVENTS)
            if cached_events is not None:
                # Re-apply live portfolio exposure on cached events
                held_symbols = await self._get_held_symbols()
                for event in cached_events:
                    event.portfolio_exposure = [
                        s for s in held_symbols
                        if s in event.related_assets or (s in ["BTC", "ETH"] and "Crypto" in event.related_assets)
                    ]
                return cached_events

        tasks = [p.fetch_events() for p in self.providers if p.is_configured()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        merged_events: Dict[str, EconomicEvent] = {}
        for res in results:
            if isinstance(res, list):
                for event in res:
                    if isinstance(event, EconomicEvent):
                        # Deduplicate by unique id
                        if event.id not in merged_events:
                            merged_events[event.id] = event

        all_events = list(merged_events.values())

        # Apply portfolio exposure
        held_symbols = await self._get_held_symbols()
        for event in all_events:
            event.portfolio_exposure = [
                s for s in held_symbols
                if s in event.related_assets or (s in ["BTC", "ETH"] and "Crypto" in event.related_assets)
            ]

        # Sort chronologically by scheduled_at ASC
        all_events.sort(key=lambda e: e.scheduled_at)

        # Cache for 30 minutes
        await global_cache.set(CACHE_KEY_EVENTS, all_events, ttl=EVENTS_CACHE_TTL)
        return all_events

    async def get_all_events(
        self,
        category: Optional[str] = None,
        importance: Optional[str] = None,
        event_status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[EconomicEvent]:
        events = await self.fetch_and_normalize_all()

        if category and category.lower() != "all":
            events = [e for e in events if e.category.lower() == category.lower()]

        if importance and importance.lower() != "all":
            events = [e for e in events if e.importance.lower() == importance.lower()]

        if event_status and event_status.lower() != "all":
            events = [e for e in events if e.event_status.lower() == event_status.lower()]

        if from_date:
            events = [e for e in events if e.scheduled_at >= from_date]

        if to_date:
            events = [e for e in events if e.scheduled_at <= to_date]

        if limit and limit > 0:
            events = events[:limit]

        return events

    async def get_upcoming_events(self, window: str = "7d", limit: int = 20) -> List[EconomicEvent]:
        """Returns upcoming scheduled economic events sorted soonest first."""
        events = await self.fetch_and_normalize_all()
        now_utc = datetime.now(timezone.utc)

        upcoming = [e for e in events if e.event_status == "upcoming" and e.scheduled_at >= now_utc]
        upcoming.sort(key=lambda e: e.scheduled_at)

        if window == "today":
            end_of_today = datetime(now_utc.year, now_utc.month, now_utc.day, 23, 59, 59, tzinfo=timezone.utc)
            upcoming = [e for e in upcoming if e.scheduled_at <= end_of_today]
        elif window == "24h":
            cutoff = now_utc + timedelta(hours=24)
            upcoming = [e for e in upcoming if e.scheduled_at <= cutoff]
        elif window == "7d":
            cutoff = now_utc + timedelta(days=7)
            upcoming = [e for e in upcoming if e.scheduled_at <= cutoff]
        elif window == "30d":
            cutoff = now_utc + timedelta(days=30)
            upcoming = [e for e in upcoming if e.scheduled_at <= cutoff]

        return upcoming[:limit]

    async def get_recent_releases(self, limit: int = 20) -> List[EconomicEvent]:
        """Returns already released economic events sorted newest first."""
        events = await self.fetch_and_normalize_all()
        now_utc = datetime.now(timezone.utc)

        recent = [e for e in events if e.event_status in ["released", "revised"] or e.scheduled_at < now_utc]
        recent.sort(key=lambda e: e.scheduled_at, reverse=True)
        return recent[:limit]

    async def get_portfolio_relevant_events(self, limit: int = 20) -> List[EconomicEvent]:
        """Returns macro events that intersect with currently held portfolio assets."""
        events = await self.fetch_and_normalize_all()
        relevant = [e for e in events if len(e.portfolio_exposure) > 0]
        # Upcoming first, then recent
        now_utc = datetime.now(timezone.utc)
        upcoming = [e for e in relevant if e.scheduled_at >= now_utc]
        recent = [e for e in relevant if e.scheduled_at < now_utc]

        upcoming.sort(key=lambda e: e.scheduled_at)
        recent.sort(key=lambda e: e.scheduled_at, reverse=True)
        return (upcoming + recent)[:limit]

    async def get_event_by_id(self, event_id: str) -> Optional[EconomicEvent]:
        events = await self.fetch_and_normalize_all()
        for e in events:
            if e.id == event_id:
                return e
        return None

    async def get_yield_curve(self) -> Optional[YieldCurveData]:
        cached: Optional[YieldCurveData] = await global_cache.get(CACHE_KEY_YIELD_CURVE)
        if cached:
            return cached

        curve = await self._treasury_provider.fetch_yield_curve()
        if curve:
            await global_cache.set(CACHE_KEY_YIELD_CURVE, curve, ttl=YIELD_CURVE_TTL)
            return curve
        return None
