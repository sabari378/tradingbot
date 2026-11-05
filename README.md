# Nirv

Nirv is an AI-assisted XAUUSD analysis and trading-orchestration platform. Its governing flow is **AI proposes, rules verify, risk controls, human approves, execution executes, everything is journaled**.

## Safety

Nirv starts in `PAPER` mode. The cloud backend never runs MetaTrader 5. A separately authenticated Windows gateway is reserved for future MT5 demo execution. Do not place broker credentials in source, `.env` files committed to Git, mobile shortcuts, or cloud configuration.

## Quick start on Ubuntu

```bash
git clone <repository-url> tradingbot
cd tradingbot
cp .env.example .env
# Replace API_KEY and other secrets before starting.
docker compose up --build -d
```

Open `http://127.0.0.1:8000/health`, `/api/v1/agents`, or `/docs`. Without a configured market provider, analysis is explicitly marked disconnected and cannot produce an executable signal.

For development without Docker:

```bash
python3 -m venv .venv
source .venv/bin/activate
make install
make backend
# In another terminal: make frontend
```

The Makefile targets are Linux-shell compatible: `make test`, `make lint`, `make backend`, `make frontend`, and `make docker-up`.

## Docker

`docker compose up --build -d` starts PostgreSQL, Redis, the backend on `8000`, and the frontend on `3000`. Session journals use a named volume so container replacement does not discard them. MT5 is intentionally excluded because MetaTrader 5 and its Python package require the Windows terminal environment.

## Architecture

The master agent coordinates chart, liquidity, volume, news, signal, and risk agents. Trade approval is a separate policy boundary before paper execution. See [docs/architecture.md](docs/architecture.md), [docs/trading-rules.md](docs/trading-rules.md), and [docs/security.md](docs/security.md).

## Roadmap

Market-structure strategies, a Next.js dashboard, the Windows MT5 demo gateway, TradingJourney synchronization, and deterministic voice intents are included as staged modules as they are implemented.
