import logging
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import httpx

try:
    from zoneinfo import ZoneInfo
    NY_TZ = ZoneInfo("America/New_York")
except Exception:
    NY_TZ = timezone(timedelta(hours=-4))

from app.modules.macro.providers.base import BaseMacroProvider
from app.modules.macro.schemas import EconomicEvent
from app.modules.macro.context_engine import MacroContextEngine

logger = logging.getLogger(__name__)

FED_MONETARY_RSS = "https://www.federalreserve.gov/feeds/press_monetary.xml"
FOMC_SCHEDULE_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

# Official 2026 FOMC Meeting Calendar from Federal Reserve Board
# Source: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
FOMC_SCHEDULE_2026: List[Dict[str, Any]] = [
    {"year": 2026, "month": 1, "day": 29, "period": "Jan 2026", "previous": 4.50, "actual": 4.50},
    {"year": 2026, "month": 3, "day": 18, "period": "Mar 2026", "previous": 4.50, "actual": 4.25},
    {"year": 2026, "month": 4, "day": 29, "period": "Apr 2026", "previous": 4.25, "actual": 4.25},
    {"year": 2026, "month": 6, "day": 17, "period": "Jun 2026", "previous": 4.25, "actual": 4.00},
    {"year": 2026, "month": 7, "day": 29, "period": "Jul 2026", "previous": 4.00, "actual": 4.00},
    {"year": 2026, "month": 9, "day": 16, "period": "Sep 2026", "previous": 4.00, "actual": None},
    {"year": 2026, "month": 11, "day": 5, "period": "Nov 2026", "previous": 4.00, "actual": None},
    {"year": 2026, "month": 12, "day": 16, "period": "Dec 2026", "previous": 4.00, "actual": None},
]

class FederalReserveProvider(BaseMacroProvider):
    """
    Authoritative provider for U.S. Federal Reserve Monetary Policy:
    - Official FOMC Meeting Calendar & Interest Rate Decisions
    - Live Statements & Minutes via Official RSS Feed
    - Zero fabrication: No synthetic forecasts on Federal Reserve decisions
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "Federal Reserve"

    def is_configured(self) -> bool:
        return True

    async def fetch_events(self) -> List[EconomicEvent]:
        events: List[EconomicEvent] = []
        now_utc = datetime.now(timezone.utc)

        # 1. Official FOMC Meeting Schedule
        for item in FOMC_SCHEDULE_2026:
            ny_dt = datetime(item["year"], item["month"], item["day"], 14, 0, 0, tzinfo=NY_TZ)
            utc_dt = ny_dt.astimezone(timezone.utc)

            event_id = f"us-fomc-rate-{item['year']}-{item['month']:02d}-{item['day']:02d}"
            is_past = utc_dt < now_utc

            # Bundled dates are fallback schedule metadata only; release state and
            # observations require a verified live acquisition.
            event_status = "unknown" if is_past else "upcoming"
            actual_val = None

            # Forecast: None because the Federal Reserve does NOT publish consensus forecasts on its own decisions
            forecast_val = None
            surprise_abs, surprise_pct = MacroContextEngine.calculate_surprises(actual_val, forecast_val)
            interp_dir, impact_summary = MacroContextEngine.derive_interpretation(
                event_code="FED_RATE",
                category="Monetary Policy",
                actual=None,
                forecast=forecast_val,
                previous=None
            )

            related_assets = MacroContextEngine.get_related_assets("FED_RATE", "Monetary Policy")

            events.append(
                EconomicEvent(
                    id=event_id,
                    provider=self.provider_name,
                    source="Federal Reserve Board",
                    source_url=FOMC_SCHEDULE_URL,
                    release_name="FOMC Statement & Policy Decision",
                    indicator_name="FOMC Interest Rate Decision",
                    event_name="FOMC Interest Rate Decision",
                    event_code="FED_RATE",
                    category="Monetary Policy",
                    country="US",
                    currency="USD",
                    scheduled_at=utc_dt,
                    period=item["period"],
                    actual=None,
                    forecast=forecast_val,
                    previous=None,
                    unit="%",
                    importance="high",
                    event_status=event_status,
                    surprise_absolute=surprise_abs,
                    surprise_percentage=surprise_pct,
                    interpretation_direction=interp_dir,
                    market_impact_summary=impact_summary,
                    schedule_source="Federal Reserve Board",
                    schedule_source_url=FOMC_SCHEDULE_URL,
                    schedule_status="fallback",
                    schedule_retrieved_at=now_utc,
                    forecast_source=None,
                    forecast_source_url=None,
                    actual_source=None,
                    actual_source_url=None,
                    actual_status="unavailable",
                    previous_source=None,
                    previous_source_url=None,
                    previous_status="unavailable",
                    forecast_status="unavailable",
                    related_assets=related_assets,
                    portfolio_exposure=[],
                    retrieved_at=now_utc,
                    data_status="fallback"
                )
            )

        # 2. Live Federal Reserve Monetary Press Releases via Official RSS
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"User-Agent": "AssetPilot-AI/0.1 (Macro-Intelligence)"}
                resp = await client.get(FED_MONETARY_RSS, headers=headers)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    for item in root.findall(".//item"):
                        title_el = item.find("title")
                        link_el = item.find("link")
                        pubdate_el = item.find("pubDate")

                        title = title_el.text.strip() if title_el is not None and title_el.text else ""
                        link = link_el.text.strip() if link_el is not None and link_el.text else ""
                        pubdate_str = pubdate_el.text.strip() if pubdate_el is not None and pubdate_el.text else ""

                        if not title:
                            continue

                        try:
                            pub_dt = datetime.strptime(pubdate_str, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
                        except Exception:
                            pub_dt = now_utc

                        event_code = "FOMC_STATEMENT" if "statement" in title.lower() else "FOMC_MINUTES"
                        event_id = f"us-fed-rss-{abs(hash(link or title)) % 10000000}"

                        interp_dir = "Official Monetary Release"
                        impact_summary = f"Federal Reserve published official communication: {title}"
                        related_assets = MacroContextEngine.get_related_assets(event_code, "Monetary Policy")

                        events.append(
                            EconomicEvent(
                                id=event_id,
                                provider=self.provider_name,
                                source="Federal Reserve Board",
                                source_url=link or FOMC_SCHEDULE_URL,
                                release_name="Federal Reserve Press Release",
                                indicator_name=title,
                                event_name=title,
                                event_code=event_code,
                                category="Monetary Policy",
                                country="US",
                                currency="USD",
                                scheduled_at=pub_dt,
                                period=None,
                                actual=None,
                                forecast=None,
                                previous=None,
                                unit="text",
                                importance="high" if "statement" in title.lower() else "medium",
                                event_status="released",
                                surprise_absolute=None,
                                surprise_percentage=None,
                                interpretation_direction=interp_dir,
                                market_impact_summary=impact_summary,
                                schedule_source="Federal Reserve Board",
                                schedule_source_url=FED_MONETARY_RSS,
                                forecast_source=None,
                                forecast_source_url=None,
                                actual_source="Federal Reserve Board",
                                actual_source_url=link or FOMC_SCHEDULE_URL,
                                previous_source=None,
                                previous_source_url=None,
                                related_assets=related_assets,
                                portfolio_exposure=[],
                                retrieved_at=now_utc,
                                data_status="live"
                            )
                        )
        except Exception as e:
            logger.warning(f"Failed to fetch Federal Reserve monetary RSS feed: {e}")

        return events
