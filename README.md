# AssetPilot AI

**AssetPilot AI** is a personal-first **AI Market Intelligence & Portfolio Assistant** covering:
- Crypto
- Stocks
- Tokenized stock exposure
- Portfolio tracking
- Financial news intelligence
- Market sentiment
- Technical analysis
- Macro-market events
- AI-assisted investment research
- Watchlists
- Opportunity & risk detection
- Weekly investment allocation assistance
- Historical signal tracking & backtesting

---

## Core Operating Philosophy

> **Data → Analysis → Evidence → Recommendation → Human Decision**

AssetPilot AI **does not** execute trades automatically or present speculative AI output as guaranteed financial advice. Every recommendation must be accompanied by supporting factors, transparent reasoning, confidence levels, risk metrics, and explicit thesis-invalidation criteria.

---

## Architecture Overview

AssetPilot AI uses a clean monorepo architecture:

```
AssetPilot AI/
├── docs/                # Architecture, roadmap, security, & engine specifications
├── frontend/            # Next.js, TypeScript, Tailwind CSS fintech UI dashboard shell
├── backend/             # Python & FastAPI modular REST API service
│   ├── app/api/v1/markets.py  # Multi-Asset Market Data API Router
│   ├── app/api/v1/portfolio.py# Read-Only Portfolio API Router
│   ├── app/modules/market_data/# OKX, Finnhub, & Tokenized Stocks Providers, Cache, & Schemas
│   ├── app/modules/portfolio/ # OKX Account Client & Portfolio Aggregator
├── scripts/             # Local development & utility scripts
├── .env.example         # Template for environment variables (NEVER COMMIT .env)
└── .gitignore           # Git ignore rules for node_modules, .venv, .env, etc.
```

---

## Phase 2A — Stocks & OKX Tokenized Stocks Foundation

- **Multi-Asset Taxonomy**:
  - `crypto`: Core cryptocurrencies (`BTC`, `ETH`, `SOL`).
  - `equity`: Traditional US equities (`AAPL`, `MSFT`, `GOOGL`, `NVDA`, `META`, `AMZN`, `TSLA`, `MSTR`, `MU`, `MRVL`).
  - `tokenized_equity`: OKX dynamically discovered tokenized stock instruments (e.g. `xGOOGL`, `xAAPL`, `xNVDA`, `xMSTR`, `xTSLA`, `xMU`, `xMRVL`, `xCRCL`, `xSPCX`, `xSKHY`, `xSNDK`, `xLITE`).
- **Critical Tokenized Stock Distinction**: Tokenized stocks are explicitly designated as `Tokenized Equity • OKX` with underlying company mappings, never represented as direct shareholder equity or 1:1 custody claims.
- **Underlying vs Tokenized Comparison**:
  - `GET /api/v1/markets/equity-comparison/{underlying_symbol}` compares traditional reference price vs OKX tokenized price.
  - Formatted strictly as `Reference Price Difference` with explicit timing and liquidity disclaimers.
- **Provider Abstraction**:
  - `FinnhubEquityProvider`: US Equities reference quotes (configurable via `FINNHUB_API_KEY` in backend `.env` with graceful reference mode when unconfigured).
  - `OKXTokenizedStocksProvider`: Dynamic instrument discovery against OKX public SPOT API.
  - `OKXMarketDataProvider`: Core crypto public feeds.
- **Multi-Asset Explorer UI**:
  - Markets page 3-tab layout: `Crypto`, `US Equities`, `Tokenized Stocks`.
  - Interactive Reference Price Comparison modal.
  - Header search bar with multi-asset category classification (`Crypto`, `Equity`, `Tokenized Equity • OKX`).

---

## Phase 1B — Secure Read-Only OKX Portfolio Integration

- **Read-Only Account API**: Authenticated synchronization of user's personal OKX holdings via official `/api/v5/account/balance` (Trading) and `/api/v5/asset/balances` (Funding) endpoints.
- **Strict Read-Only Enforcement**: Requires READ permission ONLY. Trade and Withdrawal permissions are strictly prohibited and never requested.
- **Security & Privacy Isolation**:
  - API credentials (`OKX_API_KEY`, `OKX_API_SECRET`, `OKX_API_PASSPHRASE`) exist strictly in the backend `.env` file.
  - Zero credentials appear in frontend code, browser requests, logs, or API status responses.
  - HMAC SHA-256 request signatures and authentication headers are scrubbed from log output.
- **Account Source Normalization**:
  - Distinguishes and tracks asset balances across **Trading** and **Funding** OKX accounts.
  - Aggregates total balances, available balances, and frozen balances per asset.
- **Portfolio Valuation & Allocation**:
  - Values portfolio assets using live market prices (`BTC`, `ETH`, `SOL`) and 1.0 for `USDT`.
  - Unpriced dust assets remain visible with `valuation_available=False`.

---

## Phase 1 — Live Market Data Features

- **Public OKX Provider**: Real-time ticker metrics and historical OHLCV candles for `BTC/USDT`, `ETH/USDT`, `SOL/USDT`.
- **In-Memory TTL Caching**: Tickers (10s TTL), Candles (30s TTL), Equity quotes (30s TTL), Tokenized instruments (20m TTL).
- **Zero Credentials**: 100% public REST endpoints; no API keys or secrets required for public market data.

---

## Getting Started

### Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
pytest # Run unit tests
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npx tsc --noEmit
npm run dev
```

---

## Security Principles

- **Strict Sandbox**: All project code, scripts, logs, and artifacts reside strictly in `D:\pakalfa\AssetPilot AI`.
- **Zero Credentials Committed**: `.env` is ignored by `.gitignore`.
- **Read-Only Exchange & Public APIs**: OKX public market data requires zero API keys or authentication.
