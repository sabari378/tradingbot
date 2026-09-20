PYTHON ?= python3

install:
	$(PYTHON) -m pip install -r backend/requirements.txt
	cd frontend && npm ci

test:
	$(PYTHON) -m pytest backend/tests

lint:
	$(PYTHON) -m ruff check backend

backend:
	$(PYTHON) -m uvicorn nirv.api.main:app --app-dir backend --reload --port 8000

dev: backend

frontend:
	cd frontend && npm run dev

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

migrate:
	alembic -c backend/alembic.ini upgrade head

helm-lint:
	helm lint infra/helm/nirv

helm-render:
	helm template nirv infra/helm/nirv
