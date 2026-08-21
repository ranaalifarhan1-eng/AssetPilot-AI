import re
import hashlib
from typing import List, Dict, Set
from datetime import datetime, timezone

from app.modules.news_intelligence.schemas import NewsArticle

STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is",
    "are", "was", "were", "with", "as", "by", "from", "after", "says", "report",
    "market", "news", "today", "update", "latest", "how", "what", "why", "amid"
}

SYNONYMS = {
    "federal reserve": "fed",
    "rate cut": "cut",
    "rate cuts": "cut",
    "interest rates": "rates",
    "interest rate": "rates",
    "bitcoin": "btc",
    "ethereum": "eth",
    "solana": "sol",
}

def simple_stem(word: str) -> str:
    """Lightweight suffix stripping for financial headlines."""
    if word.endswith("ing") and len(word) > 5:
        return word[:-3]
    if word.endswith("ed") and len(word) > 4:
        return word[:-2]
    if word.endswith("es") and len(word) > 4:
        return word[:-2]
    if word.endswith("s") and len(word) > 3 and not word.endswith("ss"):
        return word[:-1]
    return word

class NewsDeduplicator:
    """Deduplicates syndicated financial articles based on URL, exact ID, and headline similarity."""

    @classmethod
    def normalize_headline(cls, headline: str) -> str:
        """Removes punctuation, applies synonyms, stems, and strips stopwords for comparison."""
        cleaned = re.sub(r"[^\w\s]", " ", headline.lower())
        for orig, replacement in SYNONYMS.items():
            cleaned = cleaned.replace(orig, replacement)
        words = [simple_stem(w) for w in cleaned.split() if w and w not in STOPWORDS]
        return " ".join(words)

    @classmethod
    def token_jaccard_similarity(cls, norm_a: str, norm_b: str) -> float:
        """Calculates Jaccard word set similarity between two normalized strings."""
        set_a = set(norm_a.split())
        set_b = set(norm_b.split())
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union if union > 0 else 0.0

    @classmethod
    def generate_article_id(cls, source: str, external_id: str, url: str) -> str:
        """Generates deterministic unique ID for article."""
        raw_key = f"{source}:{external_id or url}".lower()
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def deduplicate(cls, articles: List[NewsArticle], similarity_threshold: float = 0.55) -> List[NewsArticle]:
        """
        Deduplicates a list of articles.
        Preserves original/earliest article and increments duplicate_count.
        """
        if not articles:
            return []

        # Sort by publication date descending (newest first)
        sorted_articles = sorted(articles, key=lambda a: a.published_at, reverse=True)

        deduped: List[NewsArticle] = []
        seen_urls: Set[str] = set()
        seen_ids: Set[str] = set()

        for article in sorted_articles:
            # 1. Exact URL or ID match
            if article.url in seen_urls or article.id in seen_ids:
                continue

            # 2. Headline fuzzy similarity match with existing deduped articles within 36 hours
            is_duplicate = False
            norm_curr = cls.normalize_headline(article.headline)
            
            for existing in deduped:
                # Time delta check
                time_delta = abs((existing.published_at - article.published_at).total_seconds())
                if time_delta < (36 * 3600):
                    norm_exist = cls.normalize_headline(existing.headline)
                    sim = cls.token_jaccard_similarity(norm_curr, norm_exist)
                    if sim >= similarity_threshold:
                        existing.duplicate_count += 1
                        is_duplicate = True
                        break

            if not is_duplicate:
                seen_urls.add(article.url)
                seen_ids.add(article.id)
                deduped.append(article)

        return deduped
