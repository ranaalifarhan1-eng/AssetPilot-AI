# AI Reasoning Foundation

AI reasoning is optional, disabled by default, and invoked only by `POST /api/v1/ai/analyze/{symbol}`. Page load calls the status and evidence endpoints but does not contact an LLM provider.

## Configuration

Set these variables only on the backend:

- `AI_REASONING_ENABLED=true`
- `AGENTROUTER_API_KEY=<secret>`
- `AGENTROUTER_BASE_URL=<complete OpenAI-compatible JSON endpoint>`
- `AI_PRIMARY_MODEL=<provider-supported model>`

There is deliberately no default AgentRouter URL. `GET /api/v1/ai/status` reports `provider_not_configured` until every required value is present. Provider keys remain server-side and are never returned by an endpoint or included in evidence prompts.

## Contract and safeguards

The provider receives a bounded evidence package and must return structured JSON containing a market summary, bull and bear observations, risks, portfolio context, upcoming events, invalidation conditions, evidence references, and data limitations. Output validation rejects explicit buy/sell directions, guaranteed returns, price targets, and trade-execution language. Evidence references must name an available component.

Provider calls have bounded timeouts, at most two attempts, capped `Retry-After` handling, per-asset serialization, a ten-second server-side cooldown for new fingerprints, and normalized error states. Successful results are cached for 30 minutes by asset plus evidence fingerprint. Malformed output and provider failures are returned as limitations rather than fabricated analysis.

This layer supports human research decisions. It never executes trades and is not investment advice.
