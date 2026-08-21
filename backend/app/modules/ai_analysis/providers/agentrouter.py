import asyncio
import json
import os
from typing import Optional

import httpx

from app.modules.ai_analysis.providers.base import (
    AIProviderError, AIProviderRateLimited, AIProviderTimeout, BaseAIProvider,
)
from app.modules.ai_analysis.schemas import StructuredReasoning
from app.modules.evidence_fusion.schemas import EvidencePackage

MAX_PROMPT_CHARS = 24000

SYSTEM_PROMPT = """You are AssetPilot's read-only evidence reasoning engine.
Use only facts in the supplied Evidence Package. Never invent prices, news, macro releases,
portfolio facts, or technical readings. Separate observed evidence from interpretation. State
when evidence is missing. Return only JSON matching the requested schema. Do not provide
price targets, guaranteed returns, autonomous BUY/SELL instructions, or trade execution steps."""


class AgentRouterProvider(BaseAIProvider):
    def __init__(
        self, api_key: Optional[str] = None, base_url: Optional[str] = None,
        model: Optional[str] = None, enabled: Optional[bool] = None,
        http_client: Optional[httpx.AsyncClient] = None, timeout: float = 30.0, max_attempts: int = 2,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("AGENTROUTER_API_KEY", "").strip()
        self.base_url = base_url if base_url is not None else os.getenv("AGENTROUTER_BASE_URL", "").strip()
        self.model = model if model is not None else os.getenv("AI_PRIMARY_MODEL", "gpt-5.6-sol").strip()
        env_enabled = os.getenv("AI_REASONING_ENABLED", "false").strip().lower() in ("1", "true", "yes")
        self.enabled = env_enabled if enabled is None else enabled
        self._custom_client = http_client
        self.timeout = timeout
        self.max_attempts = max(1, min(max_attempts, 2))

    @property
    def provider_name(self) -> str:
        return "AgentRouter"

    @property
    def model_name(self) -> str:
        return self.model or "gpt-5.6-sol"

    @property
    def is_configured(self) -> bool:
        return bool(self.enabled and self.api_key and self.base_url and self.model)

    async def generate_reasoning(self, evidence: EvidencePackage) -> StructuredReasoning:
        if not self.is_configured:
            raise AIProviderError("AI provider is not configured")
        evidence_json = evidence.model_dump_json(exclude={"generated_at"})
        if len(evidence_json) > MAX_PROMPT_CHARS:
            raise AIProviderError("Evidence package exceeds maximum prompt size")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": evidence_json},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        client = self._custom_client or httpx.AsyncClient(timeout=self.timeout)
        try:
            for attempt in range(self.max_attempts):
                try:
                    response = await client.post(self.base_url, headers=headers, json=payload)
                except httpx.TimeoutException as exc:
                    if attempt + 1 >= self.max_attempts:
                        raise AIProviderTimeout("AI provider timed out") from exc
                    continue
                except httpx.RequestError as exc:
                    raise AIProviderError("AI provider network failure") from exc
                if response.status_code == 429:
                    if attempt + 1 >= self.max_attempts:
                        raise AIProviderRateLimited("AI provider rate limited")
                    try:
                        delay = min(max(float(response.headers.get("Retry-After", "0")), 0.0), 2.0)
                    except ValueError:
                        delay = 0.0
                    if delay:
                        await asyncio.sleep(delay)
                    continue
                if response.status_code >= 500:
                    if attempt + 1 >= self.max_attempts:
                        raise AIProviderError("AI provider unavailable")
                    continue
                if response.status_code >= 400:
                    raise AIProviderError(f"AI provider rejected request with HTTP {response.status_code}")
                try:
                    body = response.json()
                    content = body.get("output", body)
                    if "choices" in body:
                        content = body["choices"][0]["message"]["content"]
                    if isinstance(content, str):
                        content = json.loads(content)
                    return StructuredReasoning.model_validate(content)
                except Exception as exc:
                    raise AIProviderError("AI provider returned malformed structured output") from exc
            raise AIProviderError("AI provider attempts exhausted")
        finally:
            if self._custom_client is None:
                await client.aclose()
