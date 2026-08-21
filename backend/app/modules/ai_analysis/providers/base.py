from abc import ABC, abstractmethod

from app.modules.ai_analysis.schemas import StructuredReasoning
from app.modules.evidence_fusion.schemas import EvidencePackage


class AIProviderError(RuntimeError):
    pass


class AIProviderTimeout(AIProviderError):
    pass


class AIProviderRateLimited(AIProviderError):
    pass


class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    async def generate_reasoning(self, evidence: EvidencePackage) -> StructuredReasoning: ...
