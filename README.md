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

## Ubuntu, AWS, and EKS

The cloud application is Linux-native. Backend and frontend images run as Linux containers, configuration comes from environment variables, and mutable journals are written beneath `DATA_DIR`. The Helm chart in `infra/helm/nirv` includes services, probes, resource limits, optional autoscaling, and persistent storage.

Before an EKS deployment:

1. Push the backend and frontend images to ECR and set their full repository names and immutable tags in Helm values.
2. Provision PostgreSQL and Redis as managed services and supply `DATABASE_URL` and `REDIS_URL` through Kubernetes secrets/configuration.
3. Create the `nirv-secrets` Secret through AWS Secrets Manager integration with `api-key`, `database-url`, `redis-url`, and optionally `mt5-gateway-secret`; never commit it.
4. Set the ingress hostname, TLS/ALB annotations for your cluster, and `CORS_ORIGINS` to the public HTTPS origin.
5. Keep `NIRV_MODE=PAPER` and `DEMO_TRADING_ENABLED=false` until the private MT5 gateway link has been tested.
6. Run `make helm-lint`, `make helm-render`, backend tests, and the frontend build before deployment.

The MT5 gateway remains on a Windows host. Connect EKS to it only through a private authenticated route such as a VPN/private network link, set `MT5_GATEWAY_URL` to that private endpoint, and rotate `MT5_GATEWAY_SECRET` through a secret manager. Never expose port `8100` publicly.

## Architecture

The master agent coordinates chart, liquidity, volume, news, signal, and risk agents. Trade approval is a separate policy boundary before paper execution. See [docs/architecture.md](docs/architecture.md), [docs/trading-rules.md](docs/trading-rules.md), and [docs/security.md](docs/security.md).

## Roadmap

Market-structure strategies, a Next.js dashboard, the Windows MT5 demo gateway, TradingJourney synchronization, deterministic voice intents, and AWS Terraform/Helm deployment foundations are included as staged modules as they are implemented. AWS deployment is never automatic.
