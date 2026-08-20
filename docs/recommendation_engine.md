# AssetPilot AI Recommendation Engine Specification

## Overview

AssetPilot AI rejects unexplained "BUY" or "SELL" signals. Every recommendation produced by the system is evidence-backed, transparently scored, and accompanied by explicit thesis invalidation criteria.

---

## Recommendation Actions

The engine supports four core actions:
1. **ACCUMULATE**: Strong multi-factor alignment favoring gradual position building over time.
2. **HOLD**: Existing thesis remains intact, but risk/reward ratio does not justify adding fresh capital.
3. **REDUCE**: Elevated risk metrics, broken technical support, or negative catalyst alignment.
4. **WATCH**: Dynamic setup forming; requires further data or price confirmation before action.

---

## Schema & Output Structure

Each recommendation object conforms to the following schema:

```json
{
  "asset": "BTC",
  "action": "ACCUMULATE",
  "ai_score": 78,
  "confidence": "Medium-High",
  "risk_level": "Medium",
  "price_at_recommendation": 64200.00,
  "timestamp": "2026-08-20T21:00:00Z",
  "supporting_factors": [
    "Macro environment: Federal Reserve rate pause expectations",
    "Technical structure: Holding key 200-day moving average support",
    "On-chain / Exchange reserves: Declining exchange balance trend",
    "News sentiment: Positive regulatory developments in primary markets"
  ],
  "invalidation_criteria": [
    "Daily close below $61,500 breaks technical market structure",
    "Surge in core PCE inflation data above consensus expectations"
  ],
  "sources": [
    "OKX Market Data API",
    "Federal Reserve Economic Data (FRED)",
    "Financial News Intelligence Aggregator"
  ]
}
```

---

## Scoring Methodology

The `ai_score` (0–100) is calculated by combining weighted sub-scores:
- **Technical Indicators (30%)**: Trend, Momentum (RSI), Volatility (Bollinger Bands).
- **News Intelligence & Sentiment (25%)**: Aggregated sentiment score of deduplicated news.
- **Macro & Market Structure (25%)**: Reference index correlations, interest rate environment.
- **Portfolio Context (20%)**: Current allocation concentration vs target risk limits.
