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
├── scripts/             # Local development & utility scripts
├── .env.example         # Template for environment variables (NEVER COMMIT .env)
└── .gitignore           # Git ignore rules for node_modules, .venv, .env, etc.
```

### Low-Cost Data & Reasoning Pipeline

```
Raw Data Sources (APIs / RSS / Web)
        │
        ▼
   Collection
        │
        ▼
  Normalization
        │
        ▼
  Deduplication
        │
        ▼
Relevance Filtering
        │
        ▼
 Asset Mapping
        │
        ▼
Quantitative & Technical Indicators
        │
        ▼
Selective LLM AI Reasoning
        │
        ▼
Recommendation Engine
        │
        ▼
Fintech Dashboard Shell / Alerts
```

---

## Getting Started

### Requirements
- Node.js 18+
- Python 3.10+
- Git

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
python -m app.main
```
The FastAPI backend runs on `http://127.0.0.1:8000`. Access documentation at `http://127.0.0.1:8000/docs`.

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
The Next.js dashboard runs on `http://localhost:3000`.

---

## Security Principles

- **Strict Sandbox**: All code, configuration, scripts, logs, and artifacts reside strictly within `D:\pakalfa\AssetPilot AI`.
- **Zero Credentials Committed**: `.env` is ignored by `.gitignore`.
- **Read-Only API Integrations**: Exchange and broker APIs (e.g. OKX) are strictly read-only (no withdrawal, no trade execution permissions).
- **Frontend Isolation**: Secrets and API keys are never exposed in frontend code.

---

## License

Personal project / All rights reserved.
