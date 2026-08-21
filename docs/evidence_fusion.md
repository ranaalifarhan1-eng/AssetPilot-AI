# Evidence Fusion

Phase 3B adds a deterministic, read-only evidence layer between quantitative services and optional language-model reasoning:

`Data → Deterministic Analysis → Evidence Fusion → LLM Reasoning → Human Decision`

`GET /api/v1/evidence/{symbol}` supports BTC, ETH, and SOL. It assembles market, technical, news, macro, and portfolio context with source status, timestamps, missing/stale component lists, a completeness score, and a SHA-256 evidence fingerprint.

## Reliability behavior

- Market and technical calls run concurrently and reuse the application's shared HTTP client.
- News is read from the existing news cache; evidence fusion never triggers an extra news refresh.
- Portfolio context is read from a short-lived snapshot created by the normal portfolio endpoint; it never triggers private-account synchronization.
- Macro data prefers the existing cache and uses the existing official-schedule fallback when empty.
- Each of the five evidence components contributes 20 percentage points to completeness.
- `complete`, `partial`, `stale`, `insufficient`, and `unavailable` are explicit package states. Missing data remains missing; no placeholder facts are synthesized.
- The fingerprint excludes package generation time, so identical material evidence produces an identical cache key.

Evidence fusion is analysis infrastructure only. It cannot place orders or produce autonomous trade actions.
