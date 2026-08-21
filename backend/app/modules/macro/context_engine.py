import logging
from typing import Optional, Tuple, List, Dict

logger = logging.getLogger(__name__)

# Standard exposure mapping by event code or category
EVENT_EXPOSURE_MAP: Dict[str, List[str]] = {
    "FED_RATE": ["BTC", "ETH", "US Equities", "Tokenized Equities", "Fixed Income", "USD"],
    "FOMC_STATEMENT": ["BTC", "ETH", "US Equities", "Tokenized Equities", "Fixed Income", "USD"],
    "FOMC_MINUTES": ["BTC", "ETH", "US Equities", "Tokenized Equities", "Fixed Income"],
    "CPI_YOY": ["BTC", "ETH", "US Equities", "Tokenized Equities", "Fixed Income"],
    "CPI_MOM": ["BTC", "ETH", "US Equities", "Tokenized Equities", "Fixed Income"],
    "CPI_CORE_YOY": ["BTC", "ETH", "US Equities", "Tokenized Equities", "Fixed Income"],
    "PCE_CORE_YOY": ["BTC", "ETH", "US Equities", "Tokenized Equities", "Fixed Income"],
    "PCE_YOY": ["BTC", "ETH", "US Equities", "Tokenized Equities", "Fixed Income"],
    "NFP": ["BTC", "ETH", "US Equities", "USD", "Tokenized Equities"],
    "UNEMP": ["BTC", "ETH", "US Equities", "USD"],
    "CLAIMS": ["US Equities", "Crypto", "USD"],
    "GDP_QOQ": ["US Equities", "Crypto", "Tokenized Equities"],
    "RETAIL_SALES": ["US Equities", "Consumer Goods", "Crypto"],
    "UST_10Y": ["US Equities", "BTC", "ETH", "Tokenized Equities", "Fixed Income"],
    "YIELD_CURVE": ["US Equities", "BTC", "ETH", "Tokenized Equities", "Fixed Income"],
}

CATEGORY_DEFAULT_EXPOSURES: Dict[str, List[str]] = {
    "Monetary Policy": ["BTC", "ETH", "US Equities", "Tokenized Equities", "USD"],
    "Inflation": ["BTC", "ETH", "US Equities", "Tokenized Equities", "Fixed Income"],
    "Labor": ["BTC", "ETH", "US Equities", "USD"],
    "Growth": ["US Equities", "Crypto", "Tokenized Equities"],
    "Liquidity / Rates": ["US Equities", "Crypto", "Fixed Income", "xStocks"],
}

class MacroContextEngine:
    """
    Deterministic calculation engine for:
    - Surprise magnitude (absolute & percentage)
    - Contextual economic interpretation
    - Market asset exposure mapping
    """

    @staticmethod
    def calculate_surprises(
        actual: Optional[float],
        forecast: Optional[float]
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculates absolute and percentage surprises safely.
        Returns (surprise_absolute, surprise_percentage).
        """
        if actual is None or forecast is None:
            return None, None

        surprise_abs = round(actual - forecast, 4)

        if abs(forecast) > 0.000001:
            surprise_pct = round(((actual - forecast) / abs(forecast)) * 100.0, 2)
        else:
            surprise_pct = None  # Zero forecast safety

        return surprise_abs, surprise_pct

    @staticmethod
    def derive_interpretation(
        event_code: str,
        category: str,
        actual: Optional[float],
        forecast: Optional[float],
        previous: Optional[float]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Derives deterministic economic interpretation and market impact summary.
        Informational only - NO buy/sell/trade recommendations.
        """
        if actual is None:
            if forecast is not None:
                return (
                    "Awaiting Release (Consensus Established)",
                    f"Consensus forecast is {forecast}. Market participants are positioned around this expectation."
                )
            return ("Scheduled Event", "Official release date scheduled.")

        code = event_code.upper()

        # 1. Inflation Indicators (CPI, Core CPI, PCE, Core PCE, PPI)
        if category == "Inflation" or any(c in code for c in ["CPI", "PCE", "INFLATION", "PPI"]):
            if forecast is not None:
                if actual > forecast:
                    return (
                        "Higher Than Forecast (Inflationary Pressure)",
                        "Higher inflation reading indicates persistent price pressures, increasing probability of tighter monetary policy and potential headwinds for risk assets."
                    )
                elif actual < forecast:
                    return (
                        "Lower Than Forecast (Disinflationary Progress)",
                        "Disinflationary reading shows easing price pressures, supporting expectations for monetary accommodation and historically providing tailwinds for crypto and equities."
                    )
                else:
                    return (
                        "In-Line With Consensus",
                        "Inflation reading met consensus expectations, minimizing surprise-driven market volatility."
                    )
            elif previous is not None:
                if actual > previous:
                    return ("Accelerating vs Previous Period", f"Inflation accelerated to {actual}% from previous {previous}%.")
                elif actual < previous:
                    return ("Decelerating vs Previous Period", f"Inflation slowed to {actual}% from previous {previous}%.")
                else:
                    return ("Unchanged vs Previous Period", f"Inflation remained steady at {actual}%.")

        # 2. Monetary Policy & Interest Rate Decisions
        if category == "Monetary Policy" or "FED_RATE" in code or "FOMC" in code:
            if previous is not None:
                if actual > previous:
                    diff_bps = round((actual - previous) * 100)
                    return (
                        f"Interest Rate Hike (+{diff_bps} bps)",
                        f"Federal Reserve raised the policy rate by {diff_bps} bps to {actual}%, increasing borrowing costs across credit and equity markets."
                    )
                elif actual < previous:
                    diff_bps = round((previous - actual) * 100)
                    return (
                        f"Interest Rate Cut (-{diff_bps} bps)",
                        f"Federal Reserve lowered the policy rate by {diff_bps} bps to {actual}%, injecting monetary accommodation into the financial system."
                    )
                else:
                    return (
                        f"Policy Rate Maintained ({actual}%)",
                        f"Federal Reserve maintained the target benchmark rate at {actual}%, keeping monetary stance unchanged."
                    )

        # 3. Labor Market (NFP, Unemployment Rate, Jobless Claims)
        if category == "Labor" or "NFP" in code or "UNEMP" in code or "PAYROLL" in code:
            if "UNEMP" in code:
                if forecast is not None:
                    if actual > forecast:
                        return (
                            "Higher Unemployment (Labor Market Softening)",
                            "Unemployment rose above expectations, suggesting cooling labor demand."
                        )
                    elif actual < forecast:
                        return (
                            "Lower Unemployment (Labor Market Tightness)",
                            "Unemployment fell below expectations, indicating continued labor resilience."
                        )
                    else:
                        return ("In-Line With Consensus", "Unemployment rate matched consensus expectations.")
            else:
                # NFP / Payrolls
                if forecast is not None:
                    if actual > forecast:
                        return (
                            "Stronger Labor Market (Resilient Job Creation)",
                            "Nonfarm payrolls beat consensus expectations, reflecting broad economic momentum."
                        )
                    elif actual < forecast:
                        return (
                            "Weaker Labor Market (Cooling Employment)",
                            "Job growth trailed expectations, signaling deceleration in employment expansion."
                        )
                    else:
                        return ("In-Line With Consensus", "Job additions matched consensus forecasts.")

        # 4. Growth Indicators (GDP, Retail Sales)
        if category == "Growth" or "GDP" in code or "RETAIL" in code:
            if forecast is not None:
                if actual > forecast:
                    return (
                        "Stronger Economic Growth",
                        "Economic growth exceeded projections, demonstrating robust macroeconomic activity."
                    )
                elif actual < forecast:
                    return (
                        "Slower Economic Growth",
                        "Growth came in below estimates, indicating potential moderation in economic output."
                    )
                else:
                    return ("In-Line With Consensus", "Growth figures aligned with consensus expectations.")

        # 5. Liquidity & Rates (Treasury Yields)
        if category == "Liquidity / Rates" or "UST" in code or "YIELD" in code:
            return (
                f"Benchmark Yield at {actual}%",
                "Official U.S. Treasury benchmark yield reflects current sovereign debt discount rates."
            )

        # Fallback general direction
        if forecast is not None:
            if actual > forecast:
                return ("Above Consensus Estimate", f"Released value ({actual}) exceeded forecast ({forecast}).")
            elif actual < forecast:
                return ("Below Consensus Estimate", f"Released value ({actual}) was below forecast ({forecast}).")
            else:
                return ("In-Line With Consensus", f"Released value matched forecast ({actual}).")

        return ("Official Release Published", f"Actual value recorded at {actual}.")

    @staticmethod
    def get_related_assets(event_code: str, category: str) -> List[str]:
        """Maps an event to exposed asset classes and major crypto/equities."""
        code = event_code.upper()
        if code in EVENT_EXPOSURE_MAP:
            return list(EVENT_EXPOSURE_MAP[code])
        return list(CATEGORY_DEFAULT_EXPOSURES.get(category, ["BTC", "ETH", "US Equities"]))
