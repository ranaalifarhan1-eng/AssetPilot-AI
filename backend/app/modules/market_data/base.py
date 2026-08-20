from abc import ABC, abstractmethod
from typing import List, Optional
from app.modules.market_data.schemas import NormalizedTicker, NormalizedCandle, AssetInfo

class BaseMarketDataProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the data provider"""
        pass

    @abstractmethod
    async def get_supported_assets(self) -> List[AssetInfo]:
        """Return list of supported normalized assets"""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> NormalizedTicker:
        """Fetch normalized ticker for a single normalized symbol (e.g. 'BTC')"""
        pass

    @abstractmethod
    async def get_tickers(self, symbols: List[str]) -> List[NormalizedTicker]:
        """Fetch normalized tickers for multiple symbols"""
        pass

    @abstractmethod
    async def get_candles(self, symbol: str, timeframe: str = "1H", limit: int = 100) -> List[NormalizedCandle]:
        """Fetch normalized OHLCV candles"""
        pass
