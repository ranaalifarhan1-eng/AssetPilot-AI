# AssetPilot AI Roadmap

## Phase 0: Project Foundations & Architecture Shell (CURRENT)
- [x] Monorepo structure setup (`/frontend`, `/backend`, `/docs`, `/scripts`).
- [x] Git repository initialization and remote binding.
- [x] Security policies, `.gitignore`, and `.env.example` templates.
- [x] Next.js fintech dashboard shell with demo data.
- [x] FastAPI backend shell with health endpoint.
- [x] Comprehensive architecture and domain documentation.

## Phase 1: Market Data Ingestion & Read-Only Portfolio Tracking
- [ ] Connect public market APIs (OKX public ticker, free stock price APIs).
- [ ] Implement read-only OKX account integration for real balance synchronization.
- [ ] Local storage (PostgreSQL/SQLite) for asset prices and portfolio history.
- [ ] Live updates for Overview, Portfolio, and Markets pages.

## Phase 2: News Intelligence & Technical Analysis Engine
- [ ] News feed collector (RSS feeds, crypto/stock news scrapers).
- [ ] Article deduplication and relevance scoring pipeline.
- [x] Local deterministic Technical Intelligence module (SMA, EMA, RSI, MACD, ATR, Bollinger Bands, structure, and volume context).
- [ ] Integrated Market Intelligence cards on the dashboard shell.

## Phase 3: AI Intelligence Engine & Recommendation Framework
- [x] Phase 3A deterministic quantitative and technical intelligence foundation.
- [x] Phase 3B evidence fusion and optional provider-agnostic AI reasoning foundation.
- [x] AgentRouter-compatible backend abstraction, disabled until explicitly configured.
- [x] Provenance, freshness, completeness, structured-output safety, bounded retries, and fingerprint caching.
- [ ] Evaluate and calibrate reasoning quality against a versioned evidence fixture suite.
- [ ] Broaden provider integrations only after reliability and safety evaluation.
- [ ] AI Market Brief generation from aggregated news and quantitative metrics.
- [ ] Recommendation Engine implementation (ACCUMULATE, HOLD, REDUCE, WATCH).
- [ ] Explanatory thesis builder with supporting factors and invalidation triggers.

## Phase 4: Weekly Investment Assistant & Signal History Backtesting
- [ ] Weekly allocation planner based on user budget (e.g. $20/week).
- [ ] Portfolio rebalancing and risk concentration checks.
- [ ] Recommendation logger (Signal generated, Asset, Recommendation, Entry Price, Timestamp).
- [ ] Performance tracking engine (1-day, 7-day, 30-day signal returns).
- [ ] Signal accuracy and backtesting report dashboard.

## Phase 5: Alerts & Real-time Risk Detection
- [ ] Custom price, trend, and news volatility alert engine.
- [ ] Webhook / Telegram notification integrations.
- [ ] Advanced risk matrix and portfolio stress testing.
