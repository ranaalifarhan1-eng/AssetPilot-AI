# AssetPilot AI Weekly Investment Allocation Assistant

## Purpose

The Weekly Investment Assistant helps users disciplined in Dollar-Cost Averaging (DCA) allocate their recurring weekly contribution (e.g. $20/week) across assets based on portfolio concentration, market opportunities, and risk profiles.

---

## Allocation Workflow

```
User Input: Weekly Contribution Budget (e.g., $20.00)
                        │
                        ▼
           Fetch Current Portfolio Exposure
  (Check current asset weighting vs target allocation)
                        │
                        ▼
       Evaluate Asset Pilot Recommendation Scores
    (Identify high confidence / favorable risk assets)
                        │
                        ▼
         Generate Weekly Allocation Breakdown
    (e.g., $8 BTC, $7 Stock ETF, $5 Stablecoin Reserve)
                        │
                        ▼
     Display Rationale & Risk Warnings to User
```

---

## Example Allocation Scenario

**User Input**:
- Weekly Contribution: `$20.00`
- Risk Profile: Moderate Growth
- Current Portfolio Concentration: High Crypto exposure (75%)

**System Recommendation**:

| Asset | Suggested Amount | Action | Rationale |
| :--- | :--- | :--- | :--- |
| **BTC** | `$8.00` (40%) | ACCUMULATE | Core holding; technical setup favorable. |
| **Stock Exposure (e.g. S&P 500 ETF)** | `$7.00` (35%) | ACCUMULATE | Rebalances portfolio toward equity target. |
| **USDT Reserve** | `$5.00` (25%) | RESERVE | Builds dry powder for potential pullback opportunities. |

---

## Safety Controls

- Never recommends 100% allocation into a single volatile asset.
- Automatically suggests cash/stablecoin reserve buffers during high macro volatility.
- Highlights portfolio deviation from target allocation targets.
