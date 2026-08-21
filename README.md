# AssetPilot AI

**AssetPilot AI** is a personal-first **AI Market Intelligence & Portfolio Assistant** covering:
- Crypto
- Stocks
- Tokenized stock exposure
- Portfolio tracking
- Financial news intelligence
- Macro & economic events intelligence
- Market sentiment
- Technical analysis
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
│   ├── app/api/v1/macro.py    # Macro & Economic Events Intelligence API Router
│   ├── app/api/v1/news.py     # News Intelligence API Router
│   ├── app/api/v1/markets.py  # Multi-Asset Market Data API Router
│   ├── app/api/v1/portfolio.py# Read-Only Portfolio API Router
│   ├── app/modules/macro/     # Federal Reserve, Treasury, BLS/BEA Providers & Context Engine
│   ├── app/modules/news/      # News Ingestion, Deduplication, & Entity Mapping
│   ├── app/modules/market_data/# OKX, Finnhub, & Tokenized Stocks Providers, Cache, & Schemas
│   ├── app/modules/portfolio/ # OKX Account Client & Portfolio Aggregator
├── scripts/             # Local development & utility scripts
├── .env.example         # Template for environment variables (NEVER COMMIT .env)
└── .gitignore           # Git ignore rules for node_modules, .venv, .env, etc.
```

---

## Phase 2C — Macro & Economic Events Intelligence

- **Authoritative Macroeconomic Pipeline**:
  - `Authoritative Sources → Multi-Provider Ingestion → Deduplication → Deterministic Surprise Math → Contextual Interpretation → Portfolio Intersection → UI & API`
- **Data Providers**:
  - `FederalReserveProvider`: Published 2026 FOMC Meeting Calendar, official benchmark interest rate decisions, and live press releases / minutes via official Fed RSS.
  - `TreasuryProvider`: U.S. Department of the Treasury Daily Yield Curve XML feed parsing 1M, 2M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y yields and computing 10Y-2Y curve spread & inversion flags.
  - `OfficialScheduleProvider`: Deterministic, published economic calendar for BLS CPI / Core CPI, BLS Nonfarm Payrolls & Unemployment Rate, BEA Core PCE, BEA GDP, and weekly Initial Jobless Claims.
  - `FREDProvider`: Extensible St. Louis Fed API provider for time-series releases (when `FRED_API_KEY` is configured).
- **Surprise Math & Economic Context Engine**:
  - Strict separation of `actual`, `forecast`, and `previous` fields (never substitutes previous as forecast).
  - Calculates `surprise_absolute` and safe `surprise_percentage` (protected against zero-forecast division).
  - Deterministic contextual economic interpretations (e.g. Higher than Forecast / Inflationary vs. Disinflationary) strictly as market context, never buy/sell signals.
- **Timezone Correctness**:
  - All timestamps stored in UTC (`timezone.utc`).
  - Converts published Eastern Time release hours (`08:30 ET`, `14:00 ET`) using `zoneinfo` with automatic Daylight Saving Time awareness (EDT vs EST).
- **Portfolio Exposure Intersection**:
  - Intersects macroeconomic indicators with active user holdings in the read-only portfolio cache (e.g. `['BTC', 'ETH']`) without making extra requests to OKX.
- **API Endpoints (`/api/v1/macro`)**:
  - `GET /api/v1/macro/status`: Service status and provider configuration.
  - `GET /api/v1/macro/events`: Filtered macro calendar (`category`, `importance`, `event_status`, `from_date`, `to_date`, `limit`).
  - `GET /api/v1/macro/upcoming`: Scheduled events sorted soonest first (`window: 'today' | '24h' | '7d' | '30d' | 'all'`).
  - `GET /api/v1/macro/recent`: Published events with actual vs forecast and surprise metrics.
  - `GET /api/v1/macro/portfolio`: Macro events directly affecting held portfolio assets.
  - `GET /api/v1/macro/yield-curve`: Multi-tenor U.S. Treasury yields and 10Y-2Y spread.
  - `GET /api/v1/macro/events/{event_id}`: Single event lookup.
- **Frontend Dashboard**:
  - Dedicated `/macro` dashboard with summary KPIs, Upcoming Calendar tab, Recent Releases tab, Treasury Yield Curve tab, and category/impact filter pills.
  - Homepage Overview card featuring top upcoming high-impact macroeconomic events and countdowns.

---

## Phase 2B — Financial News Intelligence Foundation

- **News Intelligence Pipeline**:
  - `Sources → Collection → Normalization → Deduplication → Entity Mapping → Relevance → Classification → Dashboard`
- **Provider Architecture**:
  - `FinnhubNewsProvider`: General market, crypto, and company-specific news (`/news?category=general`, `/news?category=crypto`, `/company-news`).
  - `RSSNewsProvider`: Curated public feeds from regulatory and macroeconomic authorities (SEC Press Releases, Federal Reserve, CoinDesk, Yahoo Finance).
- **Intelligent Entity & Tokenized Mapping**:
  - Identifies primary assets (`BTC`, `ETH`, `SOL`, `AAPL`, `MSFT`, `GOOGL`, `NVDA`, `META`, `AMZN`, `TSLA`, `MSTR`, `MU`, `MRVL`).
  - Distinguishes underlying equities from tokenized representations (`xAAPL`, `xGOOGL`, `xNVDA`, `xMSTR`, etc.).
- **Deduplication & Syndication Grouping**:
  - Consolidates syndicated copies across multiple publishers using normalized headline stemming, Jaccard token similarity, and time-window grouping.
  - Tracks `duplicate_count` to indicate syndication depth while preserving original source provenance.
- **Conservative Sentiment & Impact Classification**:
  - Deterministic sentiment scoring (`positive`, `neutral`, `negative`, `mixed`) strictly as informational metadata (never buy/sell recommendations).
  - Market impact rating (`high`, `medium`, `low`) for earnings, monetary policy (FOMC/rate decisions), regulatory actions, and major corporate events.
- **Portfolio Relevance Integration**:
  - Cross-references incoming news with active read-only OKX portfolio holdings (e.g. `Portfolio Asset: BTC`).
  - Boosts relevance ranking without triggering redundant exchange API calls.
- **API Endpoints (`/api/v1/news`)**:
  - `GET /api/v1/news`: Filtered news feed (`category`, `asset`, `source`, `sentiment`, `impact`, `portfolio_only`, `limit`, `offset`).
  - `GET /api/v1/news/assets/{symbol}`: Asset-specific news stories.
  - `GET /api/v1/news/portfolio`: News matching held OKX assets.
  - `GET /api/v1/news/status`: News providers and collection metadata.
- **Frontend News Intelligence Dashboard**:
  - Full-featured `/news` page with top metrics, category tabs, sentiment/impact dropdowns, search bar, and article cards.
  - Overview integration: Live Top 3 market intelligence stories on homepage.

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
