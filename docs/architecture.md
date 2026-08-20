# AssetPilot AI Architecture Specification

## Overview

AssetPilot AI is structured as a low-cost, high-efficiency personal market intelligence assistant. It decouples market data collection, quantitative computation, news intelligence, and AI reasoning into distinct processing layers.

---

## Processing Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                   Raw Data Ingestion                    │
│   (OKX Public API, Free Stock Data, News RSS Feeds)     │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│           Data Processing & Normalization               │
│   (Deduplication, Entity Mapping, Relevance Filter)     │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│        Quantitative & Technical Processing              │
│    (RSI, MACD, Moving Averages, Portfolio Metrics)      │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│             Selective AI LLM Reasoning                  │
│  (Batched & Filtered Inputs to minimize API Token Costs)│
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│              Recommendation Engine                      │
│ (Thesis Generation, Risk Scoring, Invalidation Criteria)│
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│             Fintech Dashboard & Alerts                  │
│       (Next.js Frontend & Backend REST API)             │
└─────────────────────────────────────────────────────────┘
```

---

## Monorepo Layout

```
AssetPilot AI/
├── backend/
│   ├── app/
│   │   ├── api/v1/                # REST endpoints
│   │   ├── core/                  # Security & configuration settings
│   │   └── modules/               # Domain logic
│   │       ├── market_data/       # Ingestion interfaces
│   │       ├── portfolio/         # Balance & asset tracking
│   │       ├── news_intelligence/ # RSS & news ingestion
│   │       ├── technical_analysis/# Indicators (RSI, SMA, MACD)
│   │       ├── ai_analysis/       # LLM prompts & summarization
│   │       ├── recommendation_engine/ # Thesis scoring
│   │       ├── alerts/            # Price & volatility triggers
│   │       ├── watchlists/        # User watchlists
│   │       ├── signal_history/    # Performance logging
│   │       └── backtesting/       # Historical accuracy evaluation
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── app/                       # Next.js App Router (pages)
│   ├── components/                # UI widgets & dashboard components
│   ├── lib/                       # API clients & utilities
│   └── package.json
├── docs/                          # Architectural specifications
└── scripts/                       # Local execution & management tools
```

---

## Cost Minimization Strategy

1. **Local Computation First**: All technical indicators (RSI, Moving Averages, Volatility) are computed locally in Python rather than requested from LLMs.
2. **Text Normalization & Deduplication**: News items and social signals are deduplicated locally using hashing and keyword relevance. Only high-impact articles are sent to the LLM.
3. **Structured Prompt Templates**: LLM calls receive compact, pre-processed data structures rather than raw HTML or full article bodies.
4. **Local Caching (Redis)**: API responses from market feeds are cached in Redis to prevent rate limiting and unnecessary network traffic.
