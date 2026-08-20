# AssetPilot AI Data Provider & API Strategy

## Overview

To keep recurring operating costs low, AssetPilot AI prioritizes free, public, and open market data providers before utilizing paid services or LLM tokens. Abstract provider interfaces are used to prevent vendor lock-in.

---

## Targeted Data Providers

| Category | Targeted Provider | Scope / Permissions | Cost Tier |
| :--- | :--- | :--- | :--- |
| **Crypto Market Data** | OKX Public REST & WebSocket API | Market tickers, orderbooks, candles, 24h volumes | Free |
| **Crypto Portfolio** | OKX Read-Only Private API | Account balances, active orders, trade history (Strictly READ-ONLY) | Free |
| **Stock & ETF Data** | Yahoo Finance (yfinance) / Alpha Vantage / Financial Modeling Prep | Stock prices, S&P 500, Nasdaq reference metrics | Free Tiers |
| **News & Intelligence** | Financial RSS Feeds, SEC Filings, CryptoPanic | Raw news articles, headlines, macro press releases | Free |
| **Macro Economics** | FRED (St. Louis Fed API) | Interest rates, inflation metrics, treasury yields | Free |
| **AI Reasoning** | OpenAI API / Anthropic API / Gemini API | Summarization, thesis generation, risk evaluation | Pay-per-use (Optimized via deduplication) |

---

## Provider Interface Design Pattern

All data access in the backend is abstracted behind abstract base classes (Python `abc.ABC`):

```python
# Conceptual design for market data provider
class BaseMarketDataProvider(ABC):
    @abstractmethod
    async def get_ticker(self, symbol: str) -> MarketTicker:
        pass

    @abstractmethod
    async def get_historical_candles(self, symbol: str, timeframe: str) -> List[Candle]:
        pass
```

This guarantees that swapping data providers (e.g. from OKX to Binance or Yahoo Finance to Polygon) requires zero changes to core domain logic or the AI reasoning engine.
