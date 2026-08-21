import httpx
import os
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from app.modules.news_intelligence.base import BaseNewsProvider
from app.modules.news_intelligence.schemas import (
    NewsArticle,
    NewsCategory,
    NewsDataStatus,
)
from app.modules.news_intelligence.entity_mapper import EntityMapper
from app.modules.news_intelligence.classifier import NewsClassifier
from app.modules.news_intelligence.deduplicator import NewsDeduplicator

logger = logging.getLogger(__name__)

class FinnhubNewsProvider(BaseNewsProvider):
    """News provider leveraging Finnhub's financial and company news endpoints."""
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 8.0, max_retries: int = 2):
        self.api_key = api_key if api_key is not None else os.getenv("FINNHUB_API_KEY", "")
        self.timeout = timeout
        self.max_retries = max_retries
        self._default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

    @property
    def provider_name(self) -> str:
        return "Finnhub"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    async def fetch_latest_news(self, limit: int = 50) -> List[NewsArticle]:
        """Fetch general and crypto market news from Finnhub."""
        if not self.is_configured:
            return []

        articles: List[NewsArticle] = []
        categories = ["general", "crypto"]

        for cat in categories:
            url = f"{self.BASE_URL}/news?category={cat}&token={self.api_key}"
            try:
                data = await self._fetch_json(url)
                if isinstance(data, list):
                    for item in data[:limit]:
                        article = self._normalize_item(item, source_category=cat)
                        if article:
                            articles.append(article)
            except Exception as e:
                logger.warning(f"Finnhub fetch error for category '{cat}': {e}")

        return articles

    async def fetch_company_news(self, symbol: str, limit: int = 20) -> List[NewsArticle]:
        """Fetch company-specific news for an equity symbol within past 7 days."""
        if not self.is_configured:
            return []

        now = datetime.now(timezone.utc)
        from_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = now.strftime("%Y-%m-%d")

        url = f"{self.BASE_URL}/company-news?symbol={symbol.upper()}&from={from_date}&to={to_date}&token={self.api_key}"
        articles: List[NewsArticle] = []

        try:
            data = await self._fetch_json(url)
            if isinstance(data, list):
                for item in data[:limit]:
                    article = self._normalize_item(item, initial_symbols=[symbol.upper()])
                    if article:
                        articles.append(article)
        except Exception as e:
            logger.warning(f"Finnhub company news fetch error for '{symbol}': {e}")

        return articles

    async def get_status(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "configured": self.is_configured,
            "endpoints": ["/news?category=general", "/news?category=crypto", "/company-news"],
            "status": "ready" if self.is_configured else "unconfigured"
        }

    async def _fetch_json(self, url: str) -> Any:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self._default_headers) as client:
            for attempt in range(1, self.max_retries + 1):
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    return resp.json()
                except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as e:
                    if attempt < self.max_retries:
                        await asyncio.sleep(0.3 * attempt)
                    else:
                        raise e

    def _normalize_item(
        self,
        raw: Dict[str, Any],
        source_category: Optional[str] = None,
        initial_symbols: Optional[List[str]] = None
    ) -> Optional[NewsArticle]:
        """Normalizes a raw Finnhub news JSON item into a standardized NewsArticle."""
        headline = (raw.get("headline") or "").strip()
        url = (raw.get("url") or "").strip()
        if not headline or not url:
            return None

        # Content safety: ensure valid HTTP/HTTPS scheme
        if not (url.startswith("http://") or url.startswith("https://")):
            return None

        summary = (raw.get("summary") or "").strip() or None
        publisher = (raw.get("source") or "Finnhub").strip()
        external_id = str(raw.get("id", ""))

        # Parse timestamp
        ts_sec = raw.get("datetime")
        if ts_sec:
            try:
                pub_dt = datetime.fromtimestamp(int(ts_sec), tz=timezone.utc)
            except Exception:
                pub_dt = datetime.now(timezone.utc)
        else:
            pub_dt = datetime.now(timezone.utc)

        # Map entities (crypto, equities, tokenized links)
        combined_text = f"{headline}. {summary or ''}"
        related_assets, related_companies = EntityMapper.map_entities(combined_text, initial_symbols=initial_symbols)

        # Classify Category, Sentiment, Impact, Relevance
        category = NewsClassifier.classify_category(combined_text, related_assets)
        if source_category == "crypto" and category == NewsCategory.GENERAL:
            category = NewsCategory.CRYPTO

        sentiment_label, sentiment_score = NewsClassifier.classify_sentiment(combined_text)
        impact_level = NewsClassifier.classify_impact(combined_text, category)
        relevance_score = NewsClassifier.calculate_relevance(
            headline=headline,
            summary=summary,
            related_assets=related_assets,
            source=self.provider_name,
            published_at=pub_dt
        )

        article_id = NewsDeduplicator.generate_article_id(
            source=self.provider_name,
            external_id=external_id,
            url=url
        )

        return NewsArticle(
            id=article_id,
            external_id=external_id,
            headline=headline,
            summary=summary,
            source=self.provider_name,
            publisher=publisher,
            url=url,
            published_at=pub_dt,
            retrieved_at=datetime.now(timezone.utc),
            category=category,
            related_assets=related_assets,
            related_companies=related_companies,
            relevance_score=relevance_score,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
            impact_level=impact_level,
            is_portfolio_relevant=False,
            portfolio_asset_match=None,
            duplicate_count=1,
            data_status=NewsDataStatus.LIVE
        )
