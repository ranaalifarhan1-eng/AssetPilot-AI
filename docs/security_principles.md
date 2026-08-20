# AssetPilot AI Security Principles

## 1. Strict Workspace Boundary
- All project operations, files, scripts, logs, build artifacts, and virtual environments must remain strictly inside `D:\pakalfa\AssetPilot AI`.
- Never execute destructive or recursive commands on parent or sibling directories.

## 2. Environment & Secret Hygiene
- **Never Commit Secrets**: `.env` files are explicitly listed in `.gitignore`. Only `.env.example` templates may be checked into Git.
- **Zero Frontend Secrets**: API keys, credentials, or private tokens must NEVER be placed in frontend code or environment variables prefixed with `NEXT_PUBLIC_` except for public API URLs.
- **Backend Secret Management**: Backend configuration uses Pydantic Settings to load secrets strictly from environment variables or local ignored `.env` files.

## 3. Read-Only Exchange & Brokerage Policy
- All exchange integrations (e.g. OKX API) must be configured with **READ-ONLY** permissions.
- **Forbidden Permissions**:
  - NO Withdrawal permissions
  - NO Trade Execution / Order Placement permissions
  - NO Transfer permissions
- AssetPilot AI is designed exclusively as an intelligence and portfolio tracking assistant. It cannot place or modify trades on live exchanges.

## 4. Input Sanitization & AI Prompt Injection Defense
- News articles and external feeds are sanitized before processing.
- Raw text ingested from the web is passed into LLM prompts as untrusted context data inside delimited blocks to prevent prompt injection attacks.
