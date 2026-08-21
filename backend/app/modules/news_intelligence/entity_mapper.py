import re
from typing import List, Dict, Tuple, Optional, Set
from app.modules.news_intelligence.schemas import RelatedAsset

# Known crypto assets dictionary
CRYPTO_ASSETS: Dict[str, Dict] = {
    "BTC": {
        "symbol": "BTC",
        "display_symbol": "BTC/USDT",
        "name": "Bitcoin",
        "asset_type": "crypto",
        "patterns": [r"\bbitcoin\b", r"\bbtc\b", r"\bsatoshi\b"],
        "tokenized_symbol": None
    },
    "ETH": {
        "symbol": "ETH",
        "display_symbol": "ETH/USDT",
        "name": "Ethereum",
        "asset_type": "crypto",
        "patterns": [r"\bethereum\b", r"\b_eth_\b", r"\bether\b", r"\bvitalik\b"],
        "tokenized_symbol": None
    },
    "SOL": {
        "symbol": "SOL",
        "display_symbol": "SOL/USDT",
        "name": "Solana",
        "asset_type": "crypto",
        "patterns": [r"\bsolana\b", r"\bsol\b"],
        "tokenized_symbol": None
    }
}

# Known US equities dictionary with tokenized mappings
EQUITY_ASSETS: Dict[str, Dict] = {
    "AAPL": {
        "symbol": "AAPL",
        "display_symbol": "AAPL",
        "name": "Apple Inc.",
        "company_name": "Apple",
        "asset_type": "equity",
        "patterns": [r"\bapple\b", r"\baapl\b", r"\biphone\b", r"\btim cook\b"],
        "tokenized_symbol": "xAAPL"
    },
    "MSFT": {
        "symbol": "MSFT",
        "display_symbol": "MSFT",
        "name": "Microsoft Corporation",
        "company_name": "Microsoft",
        "asset_type": "equity",
        "patterns": [r"\bmicrosoft\b", r"\bmsft\b", r"\bwindows\b", r"\bsatya nadella\b"],
        "tokenized_symbol": "xMSFT"
    },
    "GOOGL": {
        "symbol": "GOOGL",
        "display_symbol": "GOOGL",
        "name": "Alphabet Inc.",
        "company_name": "Alphabet",
        "asset_type": "equity",
        "patterns": [r"\bgoogle\b", r"\balphabet\b", r"\bgoogl\b", r"\bgoog\b", r"\bsundar pichai\b"],
        "tokenized_symbol": "xGOOGL"
    },
    "NVDA": {
        "symbol": "NVDA",
        "display_symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "company_name": "NVIDIA",
        "asset_type": "equity",
        "patterns": [r"\bnvidia\b", r"\bnvda\b", r"\bjensen huang\b", r"\bblackwell\b", r"\bgeforce\b"],
        "tokenized_symbol": "xNVDA"
    },
    "META": {
        "symbol": "META",
        "display_symbol": "META",
        "name": "Meta Platforms Inc.",
        "company_name": "Meta Platforms",
        "asset_type": "equity",
        "patterns": [r"\bmeta\b", r"\bfacebook\b", r"\bzuckerberg\b", r"\binstagram\b"],
        "tokenized_symbol": "xMETA"
    },
    "AMZN": {
        "symbol": "AMZN",
        "display_symbol": "AMZN",
        "name": "Amazon.com Inc.",
        "company_name": "Amazon",
        "asset_type": "equity",
        "patterns": [r"\bamazon\b", r"\bamzn\b", r"\bbezos\b", r"\bandy jassy\b", r"\baws\b"],
        "tokenized_symbol": "xAMZN"
    },
    "TSLA": {
        "symbol": "TSLA",
        "display_symbol": "TSLA",
        "name": "Tesla Inc.",
        "company_name": "Tesla",
        "asset_type": "equity",
        "patterns": [r"\btesla\b", r"\btsla\b", r"\belon musk\b", r"\bcybertruck\b"],
        "tokenized_symbol": "xTSLA"
    },
    "MSTR": {
        "symbol": "MSTR",
        "display_symbol": "MSTR",
        "name": "MicroStrategy Inc.",
        "company_name": "MicroStrategy",
        "asset_type": "equity",
        "patterns": [r"\bmicrostrategy\b", r"\bmstr\b", r"\bmichael saylor\b"],
        "tokenized_symbol": "xMSTR"
    },
    "MU": {
        "symbol": "MU",
        "display_symbol": "MU",
        "name": "Micron Technology Inc.",
        "company_name": "Micron Technology",
        "asset_type": "equity",
        "patterns": [r"\bmicron\b", r"\bmicron technology\b", r"\b_mu_\b"],
        "tokenized_symbol": "xMU"
    },
    "MRVL": {
        "symbol": "MRVL",
        "display_symbol": "MRVL",
        "name": "Marvell Technology Inc.",
        "company_name": "Marvell Technology",
        "asset_type": "equity",
        "patterns": [r"\bmarvell\b", r"\bmarvell technology\b", r"\bmrvl\b"],
        "tokenized_symbol": "xMRVL"
    }
}

class EntityMapper:
    """Extracts and maps related crypto, equities, and tokenized representations from news text."""

    @classmethod
    def map_entities(cls, text: str, initial_symbols: Optional[List[str]] = None) -> Tuple[List[RelatedAsset], List[str]]:
        """
        Extract related assets and company names from headline + summary.
        Distinguishes primary underlying asset and tokenized representation.
        """
        normalized_text = f" {text.lower()} "
        matched_symbols: Set[str] = set()
        matched_companies: Set[str] = set()
        
        # 1. Include explicit symbols supplied by provider (e.g. Finnhub company news)
        if initial_symbols:
            for s in initial_symbols:
                s_up = s.upper().strip()
                if s_up in EQUITY_ASSETS or s_up in CRYPTO_ASSETS:
                    matched_symbols.add(s_up)

        # 2. Match crypto assets
        for sym, data in CRYPTO_ASSETS.items():
            for pat in data["patterns"]:
                if re.search(pat, normalized_text, re.IGNORECASE):
                    matched_symbols.add(sym)
                    break

        # 3. Match equity assets
        for sym, data in EQUITY_ASSETS.items():
            for pat in data["patterns"]:
                if re.search(pat, normalized_text, re.IGNORECASE):
                    matched_symbols.add(sym)
                    matched_companies.add(data["company_name"])
                    break

        # 4. Secondary cross-asset heuristic (e.g. MicroStrategy Bitcoin purchase)
        if "MSTR" in matched_symbols and ("bitcoin" in normalized_text or "btc" in normalized_text):
            matched_symbols.add("BTC")

        # 5. Build RelatedAsset objects with tokenized link
        related_assets: List[RelatedAsset] = []
        for sym in matched_symbols:
            if sym in CRYPTO_ASSETS:
                c_data = CRYPTO_ASSETS[sym]
                related_assets.append(
                    RelatedAsset(
                        symbol=sym,
                        display_symbol=c_data["display_symbol"],
                        name=c_data["name"],
                        asset_type="crypto",
                        relationship_type="primary",
                        tokenized_symbol=None
                    )
                )
            elif sym in EQUITY_ASSETS:
                e_data = EQUITY_ASSETS[sym]
                related_assets.append(
                    RelatedAsset(
                        symbol=sym,
                        display_symbol=e_data["display_symbol"],
                        name=e_data["name"],
                        asset_type="equity",
                        relationship_type="primary",
                        tokenized_symbol=e_data.get("tokenized_symbol")
                    )
                )

        return related_assets, list(matched_companies)
