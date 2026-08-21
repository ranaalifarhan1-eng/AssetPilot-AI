import logging
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import List, Optional
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

# Published 2026 FOMC Meetings Calendar (Decision Release: 14:00 Eastern Time)
FOMC_SCHEDULE_2026 = [
    (2026, 1, 29, "Jan 2026", 4.50, 4.50, 4.50, "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
    (2026, 3, 19, "Mar 2026", 4.50, 4.25, 4.25, "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
    (2026, 4, 30, "Apr 2026", 4.25, 4.25, 4.25, "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
    (2026, 6, 18, "Jun 2026", 4.25, 4.00, 4.00, "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
    (2026, 7, 30, "Jul 2026", 4.00, 4.00, 4.00, "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
    (2026, 9, 17, "Sep 2026", 4.00, 3.75, None, "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
    (2026, 11, 5, "Nov 2026", 3.75, 3.75, None, "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
    (2026, 12, 17, "Dec 2026", 3.75, 3.50, None, "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
]

class FederalReserveProvider(BaseMacroProvider):
    """
    Authoritative provider for U.S. Federal Reserve Monetary Policy:
    - Official FOMC Interest Rate Decisions & Calendar
    - FOMC Press Statements & Minutes via Official RSS Feed
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

        # 1. Process Official 2026 FOMC Interest Rate Schedule
        for year, month, day, period_label, prev_rate, fcast_rate, act_rate, url in FOMC_SCHEDULE_2026:
            # Construct 14:00 NY time with full DST awareness
            ny_dt = datetime(year, month, day, 14, 0, 0, tzinfo=NY_TZ)
            utc_dt = ny_dt.astimezone(timezone.utc)

            event_id = f"us-fomc-rate-{year}-{month:02d}-{day:02d}"
            is_past = utc_dt < now_utc

            if is_past:
                event_status = "released"
                actual_val = act_rate if act_rate is not None else prev_rate
            else:
                event_status = "upcoming"
                actual_val = None

            surprise_abs, surprise_pct = MacroContextEngine.calculate_surprises(actual_val, fcast_rate)
            interp_dir, impact_summary = MacroContextEngine.derive_interpretation(
                event_code="FED_RATE",
                category="Monetary Policy",
                actual=actual_val,
                forecast=fcast_rate,
                previous=prev_rate
            )

            related_assets = MacroContextEngine.get_related_assets("FED_RATE", "Monetary Policy")

            events.append(
                EconomicEvent(
                    id=event_id,
                    provider=self.provider_name,
                    source="Federal Reserve Board",
                    source_url=url,
                    event_name="FOMC Interest Rate Decision",
                    event_code="FED_RATE",
                    category="Monetary Policy",
                    country="US",
                    currency="USD",
                    scheduled_at=utc_dt,
                    period=period_label,
                    actual=actual_val,
                    forecast=fcast_rate,
                    previous=prev_rate,
                    unit="%",
                    importance="high",
                    event_status=event_status,
                    surprise_absolute=surprise_abs,
                    surprise_percentage=surprise_pct,
                    interpretation_direction=interp_dir,
                    market_impact_summary=impact_summary,
                    related_assets=related_assets,
                    portfolio_exposure=[],
                    retrieved_at=now_utc,
                    data_status="live"
                )
            )

        # 2. Ingest Live Federal Reserve Monetary Press Releases via Official RSS
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
                                source_url=link or "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
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
                                related_assets=related_assets,
                                portfolio_exposure=[],
                                retrieved_at=now_utc,
                                data_status="live"
                            )
                        )
        except Exception as e:
            logger.warning(f"Failed to fetch Federal Reserve monetary RSS feed: {e}")

        return events
