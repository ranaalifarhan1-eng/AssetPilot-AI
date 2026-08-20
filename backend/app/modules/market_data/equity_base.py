from abc import ABC, abstractmethod
from typing import List, Optional
from app.modules.market_data.schemas import NormalizedEquityQuote, AssetInfo, NormalizedCandle

class BaseEquityMarketDataProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the equity data provider"""
        pass

    @abstractmethod
    async def get_supported_equities(self) -> List[AssetInfo]:
        """Return list of supported traditional equity assets"""
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> NormalizedEquityQuote:
        """Fetch normalized quote for a single equity symbol (e.g. 'AAPL')"""
        pass

    @abstractmethod
    async def get_quotes(self, symbols: List[str]) -> List[NormalizedEquityQuote]:
        """Fetch normalized quotes for multiple equity symbols"""
        pass

    @abstractmethod
    async def get_candles(self, symbol: str, timeframe: str = "1D", limit: int = 100) -> List[NormalizedCandle]:
        """Fetch candle data for an equity symbol"""
        pass
