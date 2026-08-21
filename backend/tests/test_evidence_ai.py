from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.ai_analysis.providers.agentrouter import AgentRouterProvider
from app.modules.ai_analysis.providers.base import AIProviderError, AIProviderRateLimited, AIProviderTimeout, BaseAIProvider
from app.modules.ai_analysis.schemas import StructuredReasoning
from app.modules.ai_analysis.service import AIAnalysisService
from app.modules.evidence_fusion.schemas import MacroEvidence, MarketEvidence, NewsEvidence, PortfolioEvidence, TechnicalEvidence
from app.modules.evidence_fusion.service import EvidenceFusionService
from app.modules.market_data.cache import MarketDataCache

NOW = datetime(2026, 8, 21, tzinfo=timezone.utc)


def reasoning_payload():
    return {
        "market_summary": "Observed evidence is mixed.", "bull_case": ["Trend is positive."],
        "bear_case": ["Momentum is weakening."], "key_risks": ["Macro event risk."],
        "portfolio_context": "The asset is held in the cached portfolio snapshot.",
        "important_upcoming_events": ["Review the scheduled release."],
        "thesis_invalidation_conditions": ["Trend state changes."],
        "evidence_used": [{"component": "market", "reference": "market.price"}],
        "data_limitations": ["News is unavailable."],
    }


async def fused_package(market_price="100", news_status="unavailable", macro_status="cached", technical_status="complete", portfolio_status="unavailable"):
    service = EvidenceFusionService(cache=MarketDataCache())
    service._market = AsyncMock(return_value=MarketEvidence(price=market_price, data_status="live", as_of=NOW))
    service._technical = AsyncMock(return_value=TechnicalEvidence(trend="bullish", data_status=technical_status, as_of=NOW))
    multi = MagicMock(timeframe_alignment="aligned_bullish")
    service._multi = AsyncMock(return_value=multi)
    service._news = AsyncMock(return_value=NewsEvidence(source_status=news_status, as_of=NOW if news_status != "unavailable" else None))
    service._macro = AsyncMock(return_value=MacroEvidence(source_status=macro_status, as_of=NOW))
    service._portfolio = AsyncMock(return_value=PortfolioEvidence(data_status=portfolio_status, as_of=NOW if portfolio_status != "unavailable" else None))
    return await service.build("btc")


@pytest.mark.asyncio
async def test_evidence_completeness_partial_and_freshness():
    package = await fused_package()
    assert package.evidence_status == "partial"
    assert package.evidence_completeness_pct == 60
    assert package.missing_components == ["news", "portfolio"]
    assert package.freshness.overall_state == "mixed"


@pytest.mark.asyncio
async def test_evidence_complete_and_fallback_stale():
    complete = await fused_package(news_status="cached", portfolio_status="cached")
    stale = await fused_package(news_status="cached", macro_status="fallback", portfolio_status="cached")
    assert complete.evidence_status == "complete"
    assert complete.evidence_completeness_pct == 100
    assert complete.freshness.overall_state == "fresh"
    assert stale.evidence_status == "stale"
    assert stale.stale_components == ["macro"]


@pytest.mark.asyncio
async def test_stale_market_is_retained_and_marked_stale():
    service = EvidenceFusionService(cache=MarketDataCache())
    service._market = AsyncMock(return_value=MarketEvidence(price="100", data_status="stale", as_of=NOW))
    service._technical = AsyncMock(return_value=TechnicalEvidence(data_status="complete", as_of=NOW))
    service._multi = AsyncMock(return_value=MagicMock(timeframe_alignment="mixed"))
    service._news = AsyncMock(return_value=NewsEvidence(source_status="cached", as_of=NOW))
    service._macro = AsyncMock(return_value=MacroEvidence(source_status="cached", as_of=NOW))
    service._portfolio = AsyncMock(return_value=PortfolioEvidence(data_status="cached", as_of=NOW))
    package = await service.build("BTC")
    assert package.market.price == "100"
    assert package.evidence_status == "stale"
    assert package.stale_components == ["market"]


@pytest.mark.asyncio
async def test_evidence_fingerprint_is_stable_and_changes_with_material_data():
    first = await fused_package()
    same = await fused_package()
    changed = await fused_package(market_price="101")
    assert first.evidence_fingerprint == same.evidence_fingerprint
    assert first.evidence_fingerprint != changed.evidence_fingerprint


@pytest.mark.asyncio
async def test_technical_insufficient_and_portfolio_unconfigured_are_missing():
    package = await fused_package(technical_status="insufficient_data", portfolio_status="unavailable")
    assert "technical" in package.missing_components
    assert "portfolio" in package.missing_components


def response(status_code, body=None, headers=None):
    result = MagicMock(status_code=status_code, headers=headers or {})
    result.json.return_value = body or {}
    return result


@pytest.mark.asyncio
async def test_agentrouter_successful_structured_response_and_no_secret_in_payload():
    client = AsyncMock()
    client.post.return_value = response(200, {"choices": [{"message": {"content": __import__("json").dumps(reasoning_payload())}}]})
    provider = AgentRouterProvider(api_key="secret", base_url="https://example.invalid/reason", model="test", enabled=True, http_client=client)
    result = await provider.generate_reasoning(await fused_package())
    assert result.market_summary.startswith("Observed")
    call = client.post.call_args
    assert call.args[0] == "https://example.invalid/reason"
    assert "secret" not in str(call.kwargs["json"])


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [{}, {"output": "not-json"}, {"output": {"market_summary": "incomplete"}}])
async def test_agentrouter_rejects_malformed_output(body):
    client = AsyncMock(); client.post.return_value = response(200, body)
    provider = AgentRouterProvider(api_key="x", base_url="https://example.invalid", model="test", enabled=True, http_client=client)
    with pytest.raises(AIProviderError, match="malformed"):
        await provider.generate_reasoning(await fused_package())


@pytest.mark.asyncio
async def test_agentrouter_timeout_rate_limit_and_server_retry_are_bounded():
    package = await fused_package()
    timeout_client = AsyncMock(); timeout_client.post.side_effect = httpx.ReadTimeout("slow")
    provider = AgentRouterProvider(api_key="x", base_url="https://example.invalid", model="test", enabled=True, http_client=timeout_client, max_attempts=2)
    with pytest.raises(AIProviderTimeout): await provider.generate_reasoning(package)
    assert timeout_client.post.await_count == 2

    limited = AsyncMock(); limited.post.return_value = response(429)
    provider = AgentRouterProvider(api_key="x", base_url="https://example.invalid", model="test", enabled=True, http_client=limited, max_attempts=2)
    with pytest.raises(AIProviderRateLimited): await provider.generate_reasoning(package)
    assert limited.post.await_count == 2

    unavailable = AsyncMock(); unavailable.post.return_value = response(503)
    provider = AgentRouterProvider(api_key="x", base_url="https://example.invalid", model="test", enabled=True, http_client=unavailable, max_attempts=2)
    with pytest.raises(AIProviderError, match="unavailable"): await provider.generate_reasoning(package)
    assert unavailable.post.await_count == 2


class FakeProvider(BaseAIProvider):
    provider_name = "mock"
    model_name = "mock-model"
    is_configured = True

    def __init__(self): self.calls = 0

    async def generate_reasoning(self, evidence):
        self.calls += 1
        return StructuredReasoning.model_validate(reasoning_payload())


@pytest.mark.asyncio
async def test_analysis_cache_prevents_duplicate_provider_call():
    evidence = await fused_package()
    evidence_service = MagicMock(); evidence_service.build = AsyncMock(return_value=evidence)
    provider = FakeProvider()
    service = AIAnalysisService(evidence_service=evidence_service, provider=provider, cache=MarketDataCache())
    first = await service.analyze("BTC"); second = await service.analyze("BTC")
    assert first.cached is False and second.cached is True
    assert provider.calls == 1


def test_unconfigured_status_and_api_rejects_unknown_asset():
    provider = AgentRouterProvider(api_key="", base_url="", enabled=False)
    status = AIAnalysisService(provider=provider).get_status()
    assert status.provider_status == "provider_not_configured"
    with TestClient(app) as client:
        assert client.get("/api/v1/ai/status").status_code == 200
        assert client.get("/api/v1/evidence/not-an-asset").status_code == 400
        serialized = str(client.get("/api/v1/ai/status").json())
        assert "AGENTROUTER_API_KEY" not in serialized and "secret" not in serialized


def test_reasoning_schema_rejects_trade_advice():
    unsafe = reasoning_payload(); unsafe["market_summary"] = "You should buy this asset."
    with pytest.raises(ValueError): StructuredReasoning.model_validate(unsafe)
