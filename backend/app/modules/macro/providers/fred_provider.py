import os
import logging
from typing import List, Optional
from datetime import datetime, timezone
import httpx

from app.modules.macro.providers.base import BaseMacroProvider
from app.modules.macro.schemas import EconomicEvent
from app.modules.macro.context_engine import MacroContextEngine

logger = logging.getLogger(__name__)

FRED_API_BASE = "https://api.stlouisfed.org/fred"

class FREDProvider(BaseMacroProvider):
    """
    Optional extensible provider for Federal Reserve Bank of St. Louis (FRED) API.
    Gracefully handles unconfigured states.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FRED_API_KEY", "")

    @property
    def provider_name(self) -> str:
        return "FRED (St. Louis Fed)"

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    async def fetch_events(self) -> List[EconomicEvent]:
        if not self.is_configured():
            logger.debug("FRED API key not configured; skipping FRED provider.")
            return []

        events: List[EconomicEvent] = []
        now_utc = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{FRED_API_BASE}/releases/dates?api_key={self.api_key}&file_type=json&limit=10"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("release_dates", []):
                        rel_id = item.get("release_id")
                        rel_name = item.get("release_name", f"FRED Release {rel_id}")
                        date_str = item.get("date")
                        if date_str:
                            dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                            events.append(
                                EconomicEvent(
                                    id=f"fred-{rel_id}-{date_str}",
                                    provider=self.provider_name,
                                    source="Federal Reserve Bank of St. Louis",
                                    source_url=f"https://fred.stlouisfed.org/release?rid={rel_id}",
                                    release_name="FRED Data Release",
                                    indicator_name=rel_name,
                                    event_name=rel_name,
                                    event_code="FRED_SERIES",
                                    category="Growth",
                                    country="US",
                                    currency="USD",
                                    scheduled_at=dt,
                                    period=None,
                                    actual=None,
                                    forecast=None,
                                    previous=None,
                                    unit="Index",
                                    importance="medium",
                                    event_status="upcoming" if dt > now_utc else "released",
                                    surprise_absolute=None,
                                    surprise_percentage=None,
                                    interpretation_direction="FRED Economic Release",
                                    market_impact_summary="Macroeconomic time series published by St. Louis Fed.",
                                    schedule_source="Federal Reserve Bank of St. Louis",
                                    schedule_source_url=f"https://fred.stlouisfed.org/release?rid={rel_id}",
                                    forecast_source=None,
                                    forecast_source_url=None,
                                    actual_source=None,
                                    actual_source_url=None,
                                    previous_source=None,
                                    previous_source_url=None,
                                    related_assets=["US Equities", "Fixed Income"],
                                    portfolio_exposure=[],
                                    retrieved_at=now_utc,
                                    data_status="live"
                                )
                            )
        except Exception as e:
            logger.warning(f"Error querying FRED API: {e}")

        return events
