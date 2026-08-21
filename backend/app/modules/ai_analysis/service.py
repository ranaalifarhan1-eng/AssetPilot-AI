import asyncio
import time
from datetime import datetime, timezone
from typing import Optional

from app.modules.ai_analysis.providers.agentrouter import AgentRouterProvider
from app.modules.ai_analysis.providers.base import AIProviderError, BaseAIProvider
from app.modules.ai_analysis.schemas import AIAnalysisResponse, AIStatusResponse
from app.modules.evidence_fusion.schemas import EvidencePackage
from app.modules.evidence_fusion.service import EvidenceFusionService
from app.modules.market_data.cache import MarketDataCache, global_cache

AI_CACHE_TTL_SECONDS = 1800.0
AI_ASSET_COOLDOWN_SECONDS = 10.0


class AIAnalysisService:
    def __init__(
        self, evidence_service: Optional[EvidenceFusionService] = None,
        provider: Optional[BaseAIProvider] = None, cache: Optional[MarketDataCache] = None,
    ):
        self.evidence_service = evidence_service or EvidenceFusionService()
        self.provider = provider or AgentRouterProvider()
        self.cache = cache or global_cache
        self._last_generated_at: Optional[datetime] = None
        self._asset_locks: dict[str, asyncio.Lock] = {}
        self._last_provider_attempt: dict[str, float] = {}

    def get_status(self) -> AIStatusResponse:
        configured = self.provider.is_configured
        return AIStatusResponse(
            enabled=getattr(self.provider, "enabled", configured), configured=configured,
            provider_status="configured" if configured else "provider_not_configured",
            ai_provider=self.provider.provider_name, ai_model=self.provider.model_name,
            last_analysis_generated_at=self._last_generated_at,
        )

    async def analyze(self, symbol: str) -> AIAnalysisResponse:
        evidence = await self.evidence_service.build(symbol)
        if not self.provider.is_configured:
            return AIAnalysisResponse(
                asset=evidence.asset, status="provider_not_configured", provider_status="provider_not_configured",
                ai_provider=self.provider.provider_name, ai_model=self.provider.model_name,
                evidence_fingerprint=evidence.evidence_fingerprint,
                data_limitations=["AI reasoning is disabled or AgentRouter configuration is incomplete."],
            )
        cache_key = f"ai_reasoning:{evidence.asset}:{evidence.evidence_fingerprint}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached.model_copy(update={"cached": True})
        lock = self._asset_locks.setdefault(evidence.asset, asyncio.Lock())
        async with lock:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached.model_copy(update={"cached": True})
            now = time.monotonic()
            since_attempt = now - self._last_provider_attempt.get(evidence.asset, 0.0)
            if since_attempt < AI_ASSET_COOLDOWN_SECONDS:
                return AIAnalysisResponse(
                    asset=evidence.asset, status="cooldown", provider_status="rate_limited",
                    ai_provider=self.provider.provider_name, ai_model=self.provider.model_name,
                    evidence_fingerprint=evidence.evidence_fingerprint,
                    data_limitations=["A new provider request for this asset is temporarily rate limited."],
                )
            self._last_provider_attempt[evidence.asset] = now
            try:
                reasoning = await self.provider.generate_reasoning(evidence)
                allowed = set(evidence.available_components)
                if any(reference.component not in allowed for reference in reasoning.evidence_used):
                    raise AIProviderError("Reasoning referenced unavailable evidence")
                generated_at = datetime.now(timezone.utc)
                result = AIAnalysisResponse(
                    asset=evidence.asset, status="complete", provider_status="configured",
                    ai_provider=self.provider.provider_name, ai_model=self.provider.model_name,
                    analysis_generated_at=generated_at, evidence_fingerprint=evidence.evidence_fingerprint,
                    reasoning=reasoning, data_limitations=reasoning.data_limitations,
                )
                self._last_generated_at = generated_at
                await self.cache.set(cache_key, result, ttl=AI_CACHE_TTL_SECONDS)
                return result
            except AIProviderError as exc:
                return AIAnalysisResponse(
                    asset=evidence.asset, status="provider_error", provider_status="error",
                    ai_provider=self.provider.provider_name, ai_model=self.provider.model_name,
                    evidence_fingerprint=evidence.evidence_fingerprint, data_limitations=[str(exc)],
                )
