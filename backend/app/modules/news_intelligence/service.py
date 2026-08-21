import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

from app.modules.news_intelligence.base import BaseNewsProvider
from app.modules.news_intelligence.finnhub_news import FinnhubNewsProvider
from app.modules.news_intelligence.rss_news import RSSNewsProvider
from app.modules.news_intelligence.schemas import (
    NewsArticle,
    NewsCategory,
    SentimentLabel,
    ImpactLevel,
    NewsDataStatus,
    NewsListResponse,
    NewsStatusResponse,
)
from app.modules.news_intelligence.deduplicator import NewsDeduplicator
from app.modules.portfolio.service import PortfolioService
from app.modules.market_data.cache import global_cache

logger = logging.getLogger(__name__)

CACHE_KEY_ARTICLES = "news_intelligence_articles"
CACHE_KEY_TIMESTAMP = "news_intelligence_last_collected"
DEFAULT_CACHE_TTL_SECONDS = 600.0  # 10 minutes cache
MIN_REFRESH_INTERVAL_SECONDS = 60.0  # 1 minute cooldown to prevent provider spamming

class NewsService:
    """Central service managing collection, deduplication, portfolio mapping, filtering, and caching."""

    def __init__(
        self,
        providers: Optional[List[BaseNewsProvider]] = None,
        portfolio_service: Optional[PortfolioService] = None,
        cache_ttl: float = DEFAULT_CACHE_TTL_SECONDS
    ):
        self.providers = providers if providers is not None else [
            FinnhubNewsProvider(),
            RSSNewsProvider()
        ]
        self.portfolio_service = portfolio_service or PortfolioService()
        self.cache_ttl = cache_ttl
        self._lock = asyncio.Lock()

    async def get_news(
        self,
        category: Optional[str] = None,
        asset: Optional[str] = None,
        source: Optional[str] = None,
        sentiment: Optional[str] = None,
        impact: Optional[str] = None,
        portfolio_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> NewsListResponse:
        """Fetch filtered news from cache or trigger live collection if cache is empty."""
        articles, last_collected, data_status = await self._get_or_collect_articles()

        # Apply filters
        filtered = articles

        if portfolio_only:
            filtered = [a for a in filtered if a.is_portfolio_relevant]

        if category and category.lower() != "all":
            cat_lower = category.lower()
            filtered = [a for a in filtered if a.category.value.lower() == cat_lower]

        if asset:
            asset_upper = asset.upper().strip()
            filtered = [
                a for a in filtered
                if any(ra.symbol.upper() == asset_upper or (ra.tokenized_symbol and ra.tokenized_symbol.upper() == asset_upper) for ra in a.related_assets)
            ]

        if source and source.lower() != "all":
            src_lower = source.lower()
            filtered = [a for a in filtered if src_lower in a.source.lower()]

        if sentiment and sentiment.lower() != "all":
            sent_lower = sentiment.lower()
            filtered = [a for a in filtered if a.sentiment_label.value.lower() == sent_lower]

        if impact and impact.lower() != "all":
            imp_lower = impact.lower()
            filtered = [a for a in filtered if a.impact_level.value.lower() == imp_lower]

        total_matching = len(filtered)
        paginated = filtered[offset : offset + limit]
        portfolio_count = sum(1 for a in articles if a.is_portfolio_relevant)

        return NewsListResponse(
            articles=paginated,
            total_count=total_matching,
            portfolio_relevant_count=portfolio_count,
            last_collected_at=last_collected,
            data_status=data_status
        )

    async def get_news_for_asset(self, symbol: str, limit: int = 20) -> NewsListResponse:
        """Fetch news specifically mentioning an asset symbol."""
        return await self.get_news(asset=symbol, limit=limit)

    async def get_portfolio_news(self, limit: int = 20) -> NewsListResponse:
        """Fetch news specifically tagged as relevant to held portfolio assets."""
        return await self.get_news(portfolio_only=True, limit=limit)

    async def get_status(self) -> NewsStatusResponse:
        """Get diagnostic information regarding configured news sources."""
        configured_sources: List[str] = []
        active_sources: List[str] = []
        provider_statuses: Dict[str, Dict[str, Any]] = {}

        for p in self.providers:
            configured_sources.append(p.provider_name)
            p_status = await p.get_status()
            provider_statuses[p.provider_name] = p_status
            if p.is_configured:
                active_sources.append(p.provider_name)

        cached_articles: Optional[List[NewsArticle]] = await global_cache.get(CACHE_KEY_ARTICLES)
        last_collected: Optional[datetime] = await global_cache.get(CACHE_KEY_TIMESTAMP)

        return NewsStatusResponse(
            configured_sources=configured_sources,
            active_sources=active_sources,
            total_cached_articles=len(cached_articles) if cached_articles else 0,
            last_successful_collection=last_collected,
            provider_statuses=provider_statuses
        )

    async def refresh_news(self, force: bool = False) -> tuple[int, bool]:
        """
        Force a fresh collection and cache update across all providers with cooldown protection.
        Returns (collected_count, cooldown_active).
        """
        async with self._lock:
            last_collected: Optional[datetime] = await global_cache.get(CACHE_KEY_TIMESTAMP)
            cached_articles: Optional[List[NewsArticle]] = await global_cache.get(CACHE_KEY_ARTICLES)
            
            if not force and last_collected is not None and cached_articles is not None:
                now = datetime.now(timezone.utc)
                last_utc = last_collected if last_collected.tzinfo else last_collected.replace(tzinfo=timezone.utc)
                elapsed = (now - last_utc).total_seconds()
                if elapsed < MIN_REFRESH_INTERVAL_SECONDS:
                    logger.debug(f"Refresh cooldown active ({elapsed:.1f}s < {MIN_REFRESH_INTERVAL_SECONDS}s). Reusing cached collection.")
                    return len(cached_articles), True

            count = await self._collect_and_cache()
            return count, False

    async def _get_or_collect_articles(self) -> tuple[List[NewsArticle], Optional[datetime], NewsDataStatus]:
        """Retrieve articles from cache, or collect fresh if cache expired/missing."""
        cached_articles: Optional[List[NewsArticle]] = await global_cache.get(CACHE_KEY_ARTICLES)
        last_collected: Optional[datetime] = await global_cache.get(CACHE_KEY_TIMESTAMP)

        if cached_articles is not None and len(cached_articles) > 0:
            return cached_articles, last_collected, NewsDataStatus.CACHED

        async with self._lock:
            # Re-check inside lock
            cached_articles = await global_cache.get(CACHE_KEY_ARTICLES)
            last_collected = await global_cache.get(CACHE_KEY_TIMESTAMP)
            if cached_articles is not None and len(cached_articles) > 0:
                return cached_articles, last_collected, NewsDataStatus.CACHED

            count = await self._collect_and_cache()
            new_articles = await global_cache.get(CACHE_KEY_ARTICLES) or []
            new_timestamp = await global_cache.get(CACHE_KEY_TIMESTAMP)
            return new_articles, new_timestamp, NewsDataStatus.LIVE

    async def _collect_and_cache(self) -> int:
        """Collect news from all providers, deduplicate, map portfolio relevance, and cache."""
        tasks = [p.fetch_latest_news(limit=60) for p in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        raw_articles: List[NewsArticle] = []
        for res in results:
            if isinstance(res, list):
                raw_articles.extend(res)
            elif isinstance(res, Exception):
                logger.warning(f"Error fetching from news provider: {res}")

        if not raw_articles:
            # Check if previous stale articles can be retained
            existing = await global_cache.get(CACHE_KEY_ARTICLES)
            if existing:
                return len(existing)
            return 0

        # Deduplicate
        deduped = NewsDeduplicator.deduplicate(raw_articles, similarity_threshold=0.75)

        # Retrieve held portfolio asset symbols for portfolio relevance tagging
        held_symbols: set[str] = set()
        try:
            summary = await self.portfolio_service.get_portfolio_summary()
            if summary and summary.assets:
                for a in summary.assets:
                    held_symbols.add(a.symbol.upper())
        except Exception as e:
            logger.debug(f"Could not load portfolio holdings for news mapping: {e}")

        # Enrich articles with portfolio relevance
        for article in deduped:
            matched_held = None
            for ra in article.related_assets:
                if ra.symbol.upper() in held_symbols:
                    matched_held = ra.symbol.upper()
                    break

            if matched_held:
                article.is_portfolio_relevant = True
                article.portfolio_asset_match = matched_held
                article.relevance_score = min(round(article.relevance_score + 0.25, 2), 1.0)
            else:
                article.is_portfolio_relevant = False
                article.portfolio_asset_match = None

        # Sort by relevance score desc and published_at desc
        deduped.sort(key=lambda a: (a.relevance_score, a.published_at), reverse=True)

        now = datetime.now(timezone.utc)
        await global_cache.set(CACHE_KEY_ARTICLES, deduped, ttl=self.cache_ttl)
        await global_cache.set(CACHE_KEY_TIMESTAMP, now, ttl=self.cache_ttl)

        return len(deduped)
