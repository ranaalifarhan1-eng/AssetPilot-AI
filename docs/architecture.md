# AssetPilot AI Architecture Specification

## Overview

AssetPilot AI is structured as a low-cost, high-efficiency personal market intelligence assistant. It decouples market data collection, quantitative computation, news intelligence, and AI reasoning into distinct processing layers.

---

## Market Data Architecture (Phase 1)

```
┌─────────────────────────────────────────────────────────┐
│                 OKX Public REST API                     │
│    (https://www.okx.com/api/v5/market/ticker & candles) │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│              OKXMarketDataProvider                      │
│    (implements BaseMarketDataProvider abstraction)      │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│              MarketDataCache (In-Memory TTL)            │
│       (10s TTL Tickers / 30s TTL Candles)               │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                MarketDataService                        │
│    (Symbol mapping, exception handling, fallback)       │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Market Router                      │
│    (/api/v1/markets/overview, /candles, /assets)        │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│             Next.js Fintech UI Dashboard                │
│    (MarketPulseCard polling & Interactive PriceChart)   │
└────────────────────────────┴────────────────────────────┘
```

---

## Normalized Data Models

All market data provider responses are mapped into standard, provider-agnostic Pydantic models:

- `NormalizedTicker`: Symbol, price, 24h open, high, low, volume, quote volume, 24h change %, timestamp, provider.
- `NormalizedCandle`: Timestamp, open, high, low, close, volume.
- `AssetInfo`: Symbol, name, category, provider symbol.

---

## Error Handling & Resiliency

- **Timeout Safety**: `httpx.AsyncClient` requests timeout after 5.0 seconds.
- **Graceful Exceptions**: External errors map to custom exceptions (`InvalidAssetError` -> 400, `InvalidTimeframeError` -> 400, `ProviderUnavailableError` -> 503).
- **Service Isolation**: The core `/api/v1/health` endpoint remains healthy even if external OKX endpoints experience transient connectivity issues.
