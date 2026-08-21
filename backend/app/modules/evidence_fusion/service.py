from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from app.modules.macro.providers.official_schedule_provider import OfficialScheduleProvider
from app.modules.macro.service import CACHE_KEY_EVENTS, CACHE_KEY_YIELD_CURVE
from app.modules.market_data.cache import MarketDataCache, global_cache
from app.modules.market_data.exceptions import InvalidAssetError
from app.modules.market_data.okx_provider import SUPPORTED_ASSETS_MAP
from app.modules.market_data.service import MarketDataService
from app.modules.news_intelligence.service import CACHE_KEY_ARTICLES, CACHE_KEY_TIMESTAMP
from app.modules.technical_analysis.service import TechnicalAnalysisService
from app.modules.technical_analysis.schemas import TechnicalAnalysisResponse
from app.modules.evidence_fusion.schemas import (
    ArticleEvidence, EvidencePackage, FreshnessEvidence, MacroEvidence, MacroEventEvidence,
    MarketEvidence, NewsEvidence, PortfolioEvidence, TechnicalEvidence,
)

COMPONENTS = ("market", "technical", "news", "macro", "portfolio")
AVAILABLE_STATUSES = {"live", "cached", "stale", "fallback", "configured", "complete", "cached_complete", "stale_complete"}
STALE_STATUSES = {"stale", "fallback"}


class EvidenceFusionService:
    def __init__(
        self,
        market_service: Optional[MarketDataService] = None,
        technical_service: Optional[TechnicalAnalysisService] = None,
        cache: Optional[MarketDataCache] = None,
    ):
        self.market_service = market_service or MarketDataService()
        self.technical_service = technical_service or TechnicalAnalysisService(market_service=self.market_service)
        self.cache = cache or global_cache

    async def build(self, symbol: str) -> EvidencePackage:
        symbol = symbol.upper()
        if symbol not in SUPPORTED_ASSETS_MAP:
            raise InvalidAssetError(symbol)

        market_result, technical_result, multi_result = await asyncio.gather(
            self._market(symbol), self._technical(symbol), self._multi(symbol), return_exceptions=True,
        )
        market = market_result if isinstance(market_result, MarketEvidence) else MarketEvidence()
        technical = technical_result if isinstance(technical_result, TechnicalEvidence) else TechnicalEvidence()
        if not isinstance(multi_result, Exception):
            technical.multi_timeframe_alignment = multi_result.timeframe_alignment
        news = await self._news(symbol)
        macro = await self._macro()
        portfolio = await self._portfolio(symbol)

        statuses = {
            "market": market.data_status,
            "technical": technical.data_status,
            "news": news.source_status,
            "macro": macro.source_status,
            "portfolio": portfolio.data_status,
        }
        available = [name for name, state in statuses.items() if state in AVAILABLE_STATUSES]
        missing = [name for name in COMPONENTS if name not in available]
        stale = [name for name, state in statuses.items() if state in STALE_STATUSES]
        completeness = len(available) * 20
        if not available:
            evidence_status = "unavailable"
        elif len(available) < 2:
            evidence_status = "insufficient"
        elif missing:
            evidence_status = "partial"
        elif stale:
            evidence_status = "stale"
        else:
            evidence_status = "complete"
        freshness = FreshnessEvidence(
            overall_state="insufficient" if not available else "stale" if stale and not missing else "mixed" if stale or missing else "fresh",
            stale_components=stale,
        )
        generated_at = datetime.now(timezone.utc)
        material = {
            "asset": symbol,
            "market": market.model_dump(mode="json"),
            "technical": technical.model_dump(mode="json"),
            "news": news.model_dump(mode="json"),
            "macro": macro.model_dump(mode="json"),
            "portfolio": portfolio.model_dump(mode="json"),
        }
        fingerprint = hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return EvidencePackage(
            asset=symbol, generated_at=generated_at, market=market, technical=technical, news=news, macro=macro,
            portfolio=portfolio, freshness=freshness, evidence_status=evidence_status,
            available_components=available, missing_components=missing, stale_components=stale,
            evidence_completeness_pct=completeness, evidence_fingerprint=fingerprint,
        )

    async def _market(self, symbol: str) -> MarketEvidence:
        ticker = await self.market_service.get_ticker(symbol)
        return MarketEvidence(
            price=ticker.price, change_24h_pct=ticker.change_24h_pct, provider=ticker.provider,
            data_status=ticker.data_status, as_of=ticker.timestamp,
        )

    async def _technical(self, symbol: str) -> TechnicalEvidence:
        result: TechnicalAnalysisResponse = await self.technical_service.analyze(symbol, "1H")
        return TechnicalEvidence(
            trend=result.trend.state, momentum=result.momentum.state, rsi_14=result.momentum.rsi_14,
            macd_state=result.momentum.macd_state, volatility=result.volatility.state,
            relative_volume=result.volume.relative_volume, swing_high=result.structure.recent_swing_high,
            swing_low=result.structure.recent_swing_low, data_status=result.data_status, as_of=result.analysis_as_of,
        )

    async def _multi(self, symbol: str):
        return await self.technical_service.analyze_multi_timeframe(symbol)

    async def _news(self, symbol: str) -> NewsEvidence:
        articles = await self.cache.get(CACHE_KEY_ARTICLES)
        collected_at = await self.cache.get(CACHE_KEY_TIMESTAMP)
        if not articles:
            return NewsEvidence(source_status="unavailable")
        relevant = [article for article in articles if any(item.symbol.upper() == symbol for item in article.related_assets)][:5]
        return NewsEvidence(
            relevant_story_count=len(relevant), positive_count=sum(a.sentiment_label.value == "positive" for a in relevant),
            negative_count=sum(a.sentiment_label.value == "negative" for a in relevant),
            neutral_count=sum(a.sentiment_label.value in ("neutral", "mixed", "unknown") for a in relevant),
            high_impact_count=sum(a.impact_level.value == "high" for a in relevant),
            top_relevant_articles=[ArticleEvidence(
                id=a.id, headline=a.headline, publisher=a.publisher, url=a.url, published_at=a.published_at,
                sentiment=a.sentiment_label.value, impact=a.impact_level.value,
            ) for a in relevant], source_status="cached", as_of=collected_at,
        )

    async def _macro(self) -> MacroEvidence:
        events = await self.cache.get(CACHE_KEY_EVENTS)
        if not events:
            events = await OfficialScheduleProvider().fetch_events()
            await self.cache.set(CACHE_KEY_EVENTS, events, ttl=1800.0)
        curve = await self.cache.get(CACHE_KEY_YIELD_CURVE)
        now = datetime.now(timezone.utc)
        upcoming = sorted(
            (event for event in events if event.scheduled_at >= now and event.importance == "high"),
            key=lambda event: event.scheduled_at,
        )
        recent = sorted(
            (event for event in events if event.event_status in ("released", "revised")),
            key=lambda event: event.scheduled_at, reverse=True,
        )[:3]
        def compact(event):
            return MacroEventEvidence(
                id=event.id, name=event.event_name, scheduled_at=event.scheduled_at, importance=event.importance,
                data_status=event.data_status, schedule_status=event.schedule_status, source=event.source,
                source_url=event.source_url,
            )
        next_event = compact(upcoming[0]) if upcoming else None
        statuses = {event.data_status for event in events}
        status = "fallback" if "fallback" in statuses else "cached" if events else "unavailable"
        as_of = max((event.retrieved_at for event in events), default=None)
        return MacroEvidence(
            next_high_impact_event=next_event,
            days_until_event=round((upcoming[0].scheduled_at - now).total_seconds() / 86400.0, 2) if upcoming else None,
            recent_releases=[compact(event) for event in recent],
            yield_10y=curve.rates.get("10Y") if curve else None,
            curve_spread_bps=curve.spread_10y_2y_bps if curve else None,
            source_status=status, as_of=as_of,
        )

    async def _portfolio(self, symbol: str) -> PortfolioEvidence:
        snapshot = await self.cache.get("portfolio_evidence_snapshot")
        if not snapshot:
            return PortfolioEvidence(data_status="unavailable", portfolio_valuation_status="unavailable")
        asset = snapshot.get("assets", {}).get(symbol)
        return PortfolioEvidence(
            held=asset is not None, balance=asset.get("balance") if asset else None,
            estimated_value_usdt=asset.get("estimated_value_usdt") if asset else None,
            allocation_pct=asset.get("allocation_pct") if asset else None,
            portfolio_valuation_status=snapshot.get("valuation_status", "unavailable"),
            data_status="cached", as_of=snapshot.get("as_of"),
        )
