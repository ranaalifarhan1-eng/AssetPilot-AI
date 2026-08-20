# AssetPilot AI Security Principles

## 1. Strict Workspace Boundary
- All project operations, files, scripts, logs, build artifacts, and virtual environments must remain strictly inside `D:\pakalfa\AssetPilot AI`.
- Never execute destructive or recursive commands on parent or sibling directories.

## 2. Environment & Secret Hygiene
- **Never Commit Secrets**: `.env` files are explicitly listed in `.gitignore`. Only `.env.example` templates may be checked into Git.
- **Zero Frontend Secrets**: API keys, credentials, or private tokens must NEVER be placed in frontend code or environment variables prefixed with `NEXT_PUBLIC_`.
- **Backend-Only Secret Storage**: `OKX_API_KEY`, `OKX_API_SECRET`, and `OKX_API_PASSPHRASE` reside strictly in the local backend runtime environment.

## 3. Read-Only Exchange & Brokerage Policy
- All exchange integrations (e.g. OKX API) must be configured with **READ-ONLY** permissions.
- **Forbidden Permissions**:
  - NO Withdrawal permissions
  - NO Trade Execution / Order Placement permissions
  - NO Transfer permissions
- AssetPilot AI is designed exclusively as an intelligence and portfolio tracking assistant. It cannot place or modify trades on live exchanges.

## 4. Secret-Safe Logging Policy
- Requests to authenticated endpoints use HMAC-SHA256 headers (`OK-ACCESS-SIGN`, `OK-ACCESS-KEY`, `OK-ACCESS-PASSPHRASE`).
- **Logging Rule**: Complete headers, request signatures, API secrets, and passphrases MUST NEVER be printed to application logs, console stdout, or error tracebacks.

## 5. Unconfigured State Safety
- When backend OKX credentials are missing or unconfigured, the application handles the unconfigured state gracefully (returning HTTP 200 with `data_status="unconfigured"`).
- Public market data, system health endpoints, and UI views operate without dependency on private credentials.
