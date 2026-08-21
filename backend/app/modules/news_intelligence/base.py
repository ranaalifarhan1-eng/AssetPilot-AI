from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.modules.news_intelligence.schemas import NewsArticle

class BaseNewsProvider(ABC):
    """Abstract base class for financial news providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the news provider."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Whether the provider has necessary API keys or configurations."""
        pass

    @abstractmethod
    async def fetch_latest_news(self, limit: int = 50) -> List[NewsArticle]:
        """Fetch general/market-wide financial news articles."""
        pass

    @abstractmethod
    async def fetch_company_news(self, symbol: str, limit: int = 20) -> List[NewsArticle]:
        """Fetch news specific to a particular equity or asset symbol."""
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get provider diagnostic metadata without exposing secrets."""
        pass
