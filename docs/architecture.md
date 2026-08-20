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

- **Timeout Safety**: `httpx.AsyncClient` requests timeout after 5.0 seconds (6.0s for authenticated account requests).
- **Graceful Exceptions**: External errors map to custom exceptions (`InvalidAssetError` -> 400, `InvalidTimeframeError` -> 400, `ProviderUnavailableError` -> 503).
- **Service Isolation**: The core `/api/v1/health` endpoint remains healthy even if external OKX endpoints experience transient connectivity issues.

---

## Portfolio Architecture (Phase 1B)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        OKX Private REST API                            │
│  (GET /api/v5/account/balance & GET /api/v5/asset/balances) READ-ONLY  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HMAC-SHA256 Signed
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        OKXAccountClient                                │
│   (Request signing, timestamp generation, header isolation, timeout)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        PortfolioService                                │
│  (Balance normalization, Trading + Funding merge, valuation, caching)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   FastAPI Portfolio Router                             │
│       (/api/v1/portfolio, /portfolio/status, /portfolio/accounts)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Next.js Portfolio UI                                │
│   (/portfolio page & Overview card: Holdings, Locations, Allocation %) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Portfolio Models & Valuation Logic

- **`AccountSourceBalance`**: `source` ('Trading' | 'Funding'), `balance`, `available`, `frozen`.
- **`PortfolioAsset`**: `symbol`, `name`, `total_balance`, `available_balance`, `frozen_balance`, `account_sources`, `price_usdt`, `estimated_value_usdt`, `valuation_available`, `allocation_pct`.
- **`PortfolioSummary`**: `total_value_usdt`, `assets`, `asset_count`, `last_synced_at`, `provider`, `data_status`, `error_message`.
- **Valuation Rule**: Assets are priced using the live `MarketDataService` ticker prices. Assets without active market pricing maintain balance visibility while marking `valuation_available = False` and excluding unpriced balance from total USDT equity calculation.
- **PnL Rule**: PnL and average cost basis are explicitly not estimated or fabricated without direct historical cost basis records.
