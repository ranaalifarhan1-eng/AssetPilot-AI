# AssetPilot AI Architecture Specification

## Overview

AssetPilot AI is structured as a low-cost, high-efficiency personal market intelligence assistant. It decouples market data collection, quantitative computation, news intelligence, and AI reasoning into distinct processing layers.

---

## Multi-Asset Market Data Architecture (Phase 2A)

```
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│     OKX Crypto SPOT     │  │  Finnhub US Equities    │  │   OKX Tokenized (xStocks)│
│  (/api/v5/market/ticker)│  │   (/api/v1/quote)       │  │ (/api/v5/public/insts)  │
└───────────┬─────────────┘  └───────────┬─────────────┘  └───────────┬─────────────┘
            │                            │                            │
            ▼                            ▼                            ▼
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│   OKXMarketDataProvider │  │  FinnhubEquityProvider  │  │OKXTokenizedStocksProvider│
└───────────┬─────────────┘  └───────────┬─────────────┘  └───────────┬─────────────┘
            │                            │                            │
            └────────────────────────────┼────────────────────────────┘
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │             MarketDataService             │
                   │  - Multi-Asset Taxonomy Normalization     │
                   │  - In-Memory TTL Cache Manager            │
                   │  - Reference Price Comparison Engine      │
                   └─────────────────────┬─────────────────────┘
                                         │
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │            FastAPI Markets Router         │
                   │  - /api/v1/markets/overview (Crypto)      │
                   │  - /api/v1/markets/assets (Catalog)       │
                   │  - /api/v1/markets/equities (Stocks)      │
                   │  - /api/v1/markets/tokenized-equities     │
                   │  - /api/v1/markets/equity-comparison      │
                   └─────────────────────┬─────────────────────┘
                                         │
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │            Next.js Multi-Asset UI         │
                   │  - 3-Tab Explorer (Crypto, Stocks, xStocks│
                   │  - Interactive Price Comparison Modal     │
                   │  - Global Multi-Asset Header Search       │
                   └───────────────────────────────────────────┘
```

---

## Multi-Asset Taxonomy & Models

All assets are categorized under strict financial taxonomy discriminators:

- **`crypto`**: Core cryptocurrencies (`BTC`, `ETH`, `SOL`).
- **`equity`**: Traditional US equities (`AAPL`, `MSFT`, `GOOGL`, `NVDA`, `META`, `AMZN`, `TSLA`, `MSTR`, `MU`, `MRVL`).
- **`tokenized_equity`**: OKX tokenized stock representations (`xGOOGL`, `xAAPL`, `xNVDA`, `xMSTR`, etc.).
- **`etf`**: Exchange-traded funds.
- **`index_reference`**: Broad benchmark references.

### Models:
- `AssetInfo`: `symbol`, `display_symbol`, `name`, `category`, `provider`, `provider_symbol`, `quote_currency`, `underlying_symbol`, `venue`, `market_status`.
- `NormalizedEquityQuote`: `symbol`, `name`, `asset_type`, `provider`, `price`, `previous_close`, `open_price`, `high`, `low`, `change_abs`, `change_pct`, `market_state`.
- `NormalizedTokenizedEquityQuote`: `symbol`, `display_symbol`, `name`, `asset_type`, `provider`, `underlying_symbol`, `underlying_name`, `price`, `open_24h`, `high_24h`, `low_24h`, `volume_24h`, `tokenized_label`.
- `EquityComparisonResponse`: `underlying_symbol`, `underlying_price`, `tokenized_symbol`, `tokenized_price`, `price_difference_abs`, `price_difference_pct`, `comparison_label="Reference Price Difference"`, `disclaimer`.

---

## Tokenized Stock Compliance & Distinction

1. **Explicit Designation**: Every tokenized asset is labeled as `Tokenized Equity • OKX`.
2. **Zero Custody / Ownership Claims**: Tokenized equities are never presented as direct share ownership or bearing shareholder voting/dividend guarantees.
3. **Reference Price Comparison**: Comparisons between a traditional stock and its OKX tokenized representation are explicitly labeled `Reference Price Difference` (never "Arbitrage Opportunity"), with clear disclosures about market hours, liquidity, and venue spread variances.

---

## Error Handling & Cache Architecture

- **In-Memory TTL Caching**:
  - Crypto Tickers: 10s TTL
  - Traditional Equity Quotes: 30s TTL
  - Tokenized Stock Tickers: 20s TTL
  - Instrument Discovery Catalog: 20m TTL
- **Provider Resilience**: If Finnhub or OKX is temporarily unreachable, other asset classes continue to render smoothly.
- **Reference Fallback**: If `FINNHUB_API_KEY` is unconfigured, traditional equities operate safely in reference mode without failing backend startup or pytest validation.
