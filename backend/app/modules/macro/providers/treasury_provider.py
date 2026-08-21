import logging
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional, Dict
import httpx

from app.modules.macro.providers.base import BaseMacroProvider
from app.modules.macro.schemas import EconomicEvent, YieldCurveData
from app.modules.macro.context_engine import MacroContextEngine

logger = logging.getLogger(__name__)

TREASURY_YIELD_XML_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?"
    "data=daily_treasury_yield_curve&field_tdr_date_value=2026"
)

XML_NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
}

TENOR_MAP = {
    "d:BC_1MONTH": "1M",
    "d:BC_2MONTH": "2M",
    "d:BC_3MONTH": "3M",
    "d:BC_6MONTH": "6M",
    "d:BC_1YEAR": "1Y",
    "d:BC_2YEAR": "2Y",
    "d:BC_3YEAR": "3Y",
    "d:BC_5YEAR": "5Y",
    "d:BC_7YEAR": "7Y",
    "d:BC_10YEAR": "10Y",
    "d:BC_20YEAR": "20Y",
    "d:BC_30YEAR": "30Y",
}

class TreasuryProvider(BaseMacroProvider):
    """
    Authoritative provider for U.S. Department of the Treasury:
    - Daily Treasury Yield Curve benchmark rates (1M through 30Y)
    - 10Y-2Y Yield Curve Spread & Inversion metrics
    """

    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "U.S. Treasury"

    def is_configured(self) -> bool:
        return True

    async def fetch_yield_curve(self) -> Optional[YieldCurveData]:
        now_utc = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"User-Agent": "AssetPilot-AI/0.1 (Treasury-Yield-Feed)"}
                resp = await client.get(TREASURY_YIELD_XML_URL, headers=headers)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    entries = root.findall(".//atom:entry", XML_NAMESPACES)
                    if not entries:
                        return None

                    # Get latest entry
                    latest_entry = entries[-1]
                    props = latest_entry.find(".//m:properties", XML_NAMESPACES)
                    if props is None:
                        return None

                    date_el = props.find("d:NEW_DATE", XML_NAMESPACES)
                    date_str = date_el.text.split("T")[0] if date_el is not None and date_el.text else str(now_utc.date())

                    rates: Dict[str, float] = {}
                    for tag, tenor in TENOR_MAP.items():
                        val_el = props.find(tag, XML_NAMESPACES)
                        if val_el is not None and val_el.text:
                            try:
                                rates[tenor] = float(val_el.text)
                            except ValueError:
                                pass

                    y10 = rates.get("10Y", 0.0)
                    y2 = rates.get("2Y", 0.0)
                    spread_bps = round((y10 - y2) * 100.0, 1)
                    curve_inversion = y2 > y10 if (y2 > 0 and y10 > 0) else False

                    return YieldCurveData(
                        date=date_str,
                        rates=rates,
                        spread_10y_2y_bps=spread_bps,
                        curve_inversion=curve_inversion,
                        source="U.S. Department of the Treasury",
                        source_url=TREASURY_YIELD_XML_URL,
                        retrieved_at=now_utc
                    )
        except Exception as e:
            logger.warning(f"Failed to fetch U.S. Treasury yield curve: {e}")

        return None

    async def fetch_events(self) -> List[EconomicEvent]:
        events: List[EconomicEvent] = []
        now_utc = datetime.now(timezone.utc)

        curve = await self.fetch_yield_curve()
        if curve and "10Y" in curve.rates:
            y10 = curve.rates["10Y"]
            y2 = curve.rates.get("2Y", 0.0)
            spread_bps = curve.spread_10y_2y_bps

            # 10Y Benchmark Rate Event
            events.append(
                EconomicEvent(
                    id=f"us-treasury-10y-{curve.date}",
                    provider=self.provider_name,
                    source="U.S. Department of the Treasury",
                    source_url=TREASURY_YIELD_XML_URL,
                    release_name="Daily Treasury Par Yield Curve Rates",
                    indicator_name="U.S. 10-Year Treasury Yield",
                    event_name="U.S. 10-Year Treasury Yield",
                    event_code="UST_10Y",
                    category="Liquidity / Rates",
                    country="US",
                    currency="USD",
                    scheduled_at=now_utc,
                    period=curve.date,
                    actual=y10,
                    forecast=None,
                    previous=None,
                    unit="%",
                    importance="high",
                    event_status="released",
                    surprise_absolute=None,
                    surprise_percentage=None,
                    interpretation_direction=f"Benchmark 10Y Yield at {y10:.2f}%",
                    market_impact_summary="10-Year Treasury yield reflects sovereign discount rates, influencing equity multiples, mortgage rates, and crypto liquidity.",
                    schedule_source="U.S. Department of the Treasury",
                    schedule_source_url=TREASURY_YIELD_XML_URL,
                    forecast_source=None,
                    forecast_source_url=None,
                    actual_source="U.S. Department of the Treasury",
                    actual_source_url=TREASURY_YIELD_XML_URL,
                    previous_source=None,
                    previous_source_url=None,
                    related_assets=MacroContextEngine.get_related_assets("UST_10Y", "Liquidity / Rates"),
                    portfolio_exposure=[],
                    retrieved_at=now_utc,
                    data_status="live"
                )
            )

            # 10Y-2Y Yield Curve Spread Event
            curve_status = "Inverted (Recession Indicator)" if curve.curve_inversion else "Normal / Upward Sloping"
            events.append(
                EconomicEvent(
                    id=f"us-treasury-spread-10y2y-{curve.date}",
                    provider=self.provider_name,
                    source="U.S. Department of the Treasury",
                    source_url=TREASURY_YIELD_XML_URL,
                    release_name="Daily Treasury Par Yield Curve Rates",
                    indicator_name="10Y - 2Y Yield Curve Spread",
                    event_name="10Y - 2Y Yield Curve Spread",
                    event_code="YIELD_CURVE",
                    category="Liquidity / Rates",
                    country="US",
                    currency="USD",
                    scheduled_at=now_utc,
                    period=curve.date,
                    actual=spread_bps,
                    forecast=None,
                    previous=None,
                    unit="bps",
                    importance="medium",
                    event_status="released",
                    surprise_absolute=None,
                    surprise_percentage=None,
                    interpretation_direction=f"Spread: {spread_bps:+.1f} bps ({curve_status})",
                    market_impact_summary=f"Yield curve spread (10Y minus 2Y) is {spread_bps:+.1f} bps. Curve inversion indicates historical recession signal.",
                    schedule_source="U.S. Department of the Treasury",
                    schedule_source_url=TREASURY_YIELD_XML_URL,
                    forecast_source=None,
                    forecast_source_url=None,
                    actual_source="U.S. Department of the Treasury",
                    actual_source_url=TREASURY_YIELD_XML_URL,
                    previous_source=None,
                    previous_source_url=None,
                    related_assets=MacroContextEngine.get_related_assets("YIELD_CURVE", "Liquidity / Rates"),
                    portfolio_exposure=[],
                    retrieved_at=now_utc,
                    data_status="live"
                )
            )

        return events
