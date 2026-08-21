# Nirv

Nirv is an AI-assisted XAUUSD analysis and trading-orchestration platform. Its governing flow is **AI proposes, rules verify, risk controls, human approves, execution executes, everything is journaled**.

## Safety

Nirv starts in `PAPER` mode. The cloud backend never runs MetaTrader 5. A separately authenticated Windows gateway is reserved for future MT5 demo execution. Do not place broker credentials in source, `.env` files committed to Git, mobile shortcuts, or cloud configuration.

## Quick start

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn nirv.api.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/health`, `/api/v1/agents`, or `/docs`. Without a configured market provider, analysis is explicitly marked disconnected and cannot produce an executable signal.

## Docker

`docker compose up --build` starts PostgreSQL, Redis, the backend on `8000`, and the frontend on `3000`. MT5 is intentionally excluded because it runs on Windows beside the terminal.

## Architecture

The master agent coordinates chart, liquidity, volume, news, signal, and risk agents. Trade approval is a separate policy boundary before paper execution. See [docs/architecture.md](docs/architecture.md), [docs/trading-rules.md](docs/trading-rules.md), and [docs/security.md](docs/security.md).

## Roadmap

Market-structure strategies, a Next.js dashboard, the Windows MT5 demo gateway, TradingJourney synchronization, deterministic voice intents, and AWS Terraform/Helm deployment foundations are included as staged modules as they are implemented. AWS deployment is never automatic.
