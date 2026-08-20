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
│   ├── app/api/v1/markets.py  # Live OKX Market Data API Router
│   ├── app/modules/market_data/# OKX Market Provider, Cache, & Schemas
├── scripts/             # Local development & utility scripts
├── .env.example         # Template for environment variables (NEVER COMMIT .env)
└── .gitignore           # Git ignore rules for node_modules, .venv, .env, etc.
```

---

## Phase 1 — Live Market Data Features

- **Public OKX Provider**: Real-time ticker metrics and historical OHLCV candles for `BTC/USDT`, `ETH/USDT`, `SOL/USDT`.
- **In-Memory TTL Caching**: Tickers (10s TTL) and Candles (30s TTL) cached locally to prevent API rate limits.
- **REST Endpoints**:
  - `GET /api/v1/markets/overview`: Normalized tickers for core assets.
  - `GET /api/v1/markets/assets`: List of supported assets.
  - `GET /api/v1/markets/{symbol}`: Single asset ticker data.
  - `GET /api/v1/markets/{symbol}/candles`: Historical OHLCV candle trends.
- **Fintech Dashboard Integration**: Live Market Pulse cards on Overview page and interactive Price Trend charts on Markets page.
- **Zero Credentials**: 100% public REST endpoints; no OKX API keys or secrets required.

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
  - Values portfolio assets using live Phase 1 market prices (`BTC`, `ETH`, `SOL`) and 1.0 for `USDT`.
  - For assets without available market pricing, balances are displayed, `valuation_available` is set to `False`, and unpriced value is safely excluded from total equity calculations.
- **PnL / Cost Basis Limitation**: Cost basis and historical PnL are explicitly not guessed or fabricated.
- **Portfolio Endpoints**:
  - `GET /api/v1/portfolio`: Aggregated holdings, USDT valuation, and allocation percentages.
  - `GET /api/v1/portfolio/status`: Safe status metadata (`configured`, `provider`, `read_only_expected`, `last_successful_sync`, `connection_status`).
  - `GET /api/v1/portfolio/accounts`: Account source areas (`Trading`, `Funding`).

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
python -m app.main
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
