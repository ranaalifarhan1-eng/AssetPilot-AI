from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.modules.macro.schemas import EconomicEvent, YieldCurveData

class BaseMacroProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the data provider."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether the provider is configured and ready."""
        pass

    @abstractmethod
    async def fetch_events(self) -> List[EconomicEvent]:
        """Fetch economic events from the provider."""
        pass

    async def fetch_yield_curve(self) -> Optional[YieldCurveData]:
        """Optional method for providers that supply sovereign yield curve data."""
        return None
