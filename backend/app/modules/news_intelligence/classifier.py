import re
from datetime import datetime, timezone
from typing import Tuple, List, Optional

from app.modules.news_intelligence.schemas import (
    NewsCategory,
    SentimentLabel,
    ImpactLevel,
    RelatedAsset,
)

# Financial sentiment lexicons
POSITIVE_TERMS = [
    r"\brecord high\b", r"\bsurges?\b", r"\bsoars?\b", r"\bprofit surges?\b",
    r"\bbeats? (estimates|earnings|forecast)\b", r"\boutperforms?\b", r"\bgrowth\b",
    r"\bapproval\b", r"\bapproved\b", r"\bupgrade(d|s)?\b", r"\binflow(s)?\b",
    r"\bpartnership\b", r"\bexpansion\b", r"\bbreakthrough\b", r"\brally\b",
    r"\bstrong revenue\b", r"\bdividend increase\b", r"\bbullish\b", r"\bgains?\b"
]

NEGATIVE_TERMS = [
    r"\blawsuit(s)?\b", r"\bprobe(s)?\b", r"\binvestigation(s)?\b", r"\bfine(d|s)?\b",
    r"\bpenalty\b", r"\bmisses? (estimates|earnings|forecast)\b", r"\bdowngrade(d|s)?\b",
    r"\bhack(ed)?\b", r"\bexploit(ed)?\b", r"\binsolven(t|cy)\b", r"\blayoffs?\b",
    r"\bslumps?\b", r"\bplunges?\b", r"\bbans?\b", r"\bsanctions?\b", r"\bdecline(d|s)?\b",
    r"\bwarning\b", r"\bbearish\b", r"\bloss(es)?\b", r"\bbreach\b", r"\bdefault(ed)?\b"
]

# Category keyword mappings
CATEGORY_PATTERNS = {
    NewsCategory.MONETARY_POLICY: [
        r"\bfederal reserve\b", r"\bfed\b", r"\bfomc\b", r"\binterest rates?\b",
        r"\brate (cut|hike|decision)\b", r"\bjerome powell\b", r"\bcentral bank\b", r"\bquantitative\b"
    ],
    NewsCategory.REGULATION: [
        r"\bsec\b", r"\bsecurities and exchange commission\b", r"\bcftc\b", r"\bdoj\b",
        r"\bregulat(ion|ory|or|ors)\b", r"\benforcement\b", r"\bcompliance\b", r"\blawsuit\b"
    ],
    NewsCategory.EARNINGS: [
        r"\bearnings\b", r"\bquarterly (results|revenue|profit|loss)\b", r"\beps\b",
        r"\bguidance\b", r"\bfinancial results\b", r"\b10-q\b", r"\b10-k\b", r"\bbeat estimates\b"
    ],
    NewsCategory.ETF_INSTITUTIONAL: [
        r"\betf\b", r"\bspot etf\b", r"\bblackrock\b", r"\bfidelity\b", r"\bgrayscale\b",
        r"\binstitutional (inflow|adoption|investor)\b", r"\bcustody\b"
    ],
    NewsCategory.CRYPTO: [
        r"\bbitcoin\b", r"\bbtc\b", r"\bethereum\b", r"\beth\b", r"\bsolana\b", r"\bsol\b",
        r"\bcrypto\b", r"\bblockchain\b", r"\bweb3\b", r"\btokenized\b", r"\bmining\b", r"\bdefi\b"
    ],
    NewsCategory.MACRO: [
        r"\binflation\b", r"\bcpi\b", r"\bpce\b", r"\bgdp\b", r"\bunemployment\b",
        r"\btreasury yields?\b", r"\brecession\b", r"\beconom(y|ic)\b"
    ],
    NewsCategory.TECHNOLOGY: [
        r"\bartificial intelligence\b", r"\bai\b", r"\bsemiconductor\b", r"\bchip(s)?\b",
        r"\bcloud\b", r"\bsoftware\b", r"\bquantum\b", r"\bgpu(s)?\b"
    ]
}

# High impact triggers
HIGH_IMPACT_PATTERNS = [
    r"\bearnings\b", r"\brate (cut|hike|decision)\b", r"\bfomc\b", r"\bsec (charges|lawsuit|action|probe)\b",
    r"\bacquisition\b", r"\bmerger\b", r"\bspot etf approval\b", r"\bbankruptcy\b",
    r"\binflation (surges|drops)\b", r"\bcpi\b", r"\bgdp\b", r"\binvestigation\b"
]

MEDIUM_IMPACT_PATTERNS = [
    r"\bproduct launch\b", r"\bpartnership\b", r"\bupgrade\b", r"\bdowngrade\b",
    r"\bprice target\b", r"\brevenue growth\b", r"\bguidance\b", r"\bnew feature\b"
]

class NewsClassifier:
    """Classifies category, sentiment, market impact, and relevance score deterministically."""

    @classmethod
    def classify_category(cls, text: str, related_assets: List[RelatedAsset]) -> NewsCategory:
        """Determines the most applicable NewsCategory."""
        text_lower = text.lower()
        
        for category, patterns in CATEGORY_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text_lower, re.IGNORECASE):
                    return category
                    
        # Check if company asset is present
        has_equity = any(a.asset_type == "equity" for a in related_assets)
        if has_equity:
            return NewsCategory.COMPANY
            
        has_crypto = any(a.asset_type == "crypto" for a in related_assets)
        if has_crypto:
            return NewsCategory.CRYPTO

        return NewsCategory.GENERAL

    @classmethod
    def classify_sentiment(cls, text: str) -> Tuple[SentimentLabel, float]:
        """
        Conservative rule-based sentiment metadata.
        Returns (SentimentLabel, sentiment_score between -1.0 and 1.0).
        """
        text_lower = text.lower()
        pos_hits = sum(1 for pat in POSITIVE_TERMS if re.search(pat, text_lower, re.IGNORECASE))
        neg_hits = sum(1 for pat in NEGATIVE_TERMS if re.search(pat, text_lower, re.IGNORECASE))

        if pos_hits > 0 and neg_hits > 0:
            score = (pos_hits - neg_hits) / max(pos_hits + neg_hits, 1)
            return (SentimentLabel.MIXED if abs(score) < 0.3 else (SentimentLabel.POSITIVE if score > 0 else SentimentLabel.NEGATIVE)), round(score, 2)
        elif pos_hits > 0:
            score = min(0.3 + (pos_hits * 0.2), 1.0)
            return SentimentLabel.POSITIVE, round(score, 2)
        elif neg_hits > 0:
            score = max(-0.3 - (neg_hits * 0.2), -1.0)
            return SentimentLabel.NEGATIVE, round(score, 2)
        else:
            return SentimentLabel.NEUTRAL, 0.0

    @classmethod
    def classify_impact(cls, text: str, category: NewsCategory) -> ImpactLevel:
        """Determines the informational impact level of the news article."""
        text_lower = text.lower()
        
        # High impact checks
        if category in [NewsCategory.MONETARY_POLICY, NewsCategory.EARNINGS]:
            return ImpactLevel.HIGH
            
        for pat in HIGH_IMPACT_PATTERNS:
            if re.search(pat, text_lower, re.IGNORECASE):
                return ImpactLevel.HIGH

        # Medium impact checks
        for pat in MEDIUM_IMPACT_PATTERNS:
            if re.search(pat, text_lower, re.IGNORECASE):
                return ImpactLevel.MEDIUM

        if category in [NewsCategory.REGULATION, NewsCategory.ETF_INSTITUTIONAL, NewsCategory.MACRO]:
            return ImpactLevel.MEDIUM

        return ImpactLevel.LOW

    @classmethod
    def calculate_relevance(
        cls,
        headline: str,
        summary: Optional[str],
        related_assets: List[RelatedAsset],
        source: str,
        published_at: datetime
    ) -> float:
        """Calculates bounded deterministic relevance score between 0.0 and 1.0."""
        score = 0.4  # Base relevance

        # Entity presence bonus
        if len(related_assets) > 0:
            score += 0.25
            # Bonus if entity is directly mentioned in headline
            for a in related_assets:
                if a.symbol.lower() in headline.lower() or (a.name and a.name.lower() in headline.lower()):
                    score += 0.15
                    break

        # Authoritative source bonus
        if "SEC" in source or "Federal Reserve" in source:
            score += 0.1
        elif "Finnhub" in source or "Bloomberg" in source or "Reuters" in source:
            score += 0.05

        # Recency decay (hours old)
        now = datetime.now(timezone.utc)
        pub_utc = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
        hours_old = max(0.0, (now - pub_utc).total_seconds() / 3600.0)
        
        if hours_old < 6:
            score += 0.05
        elif hours_old > 48:
            score -= 0.1
        elif hours_old > 168:
            score -= 0.2

        return max(0.1, min(round(score, 2), 1.0))
