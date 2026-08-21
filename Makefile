install:
	python -m pip install -r backend/requirements.txt

test:
	python -m pytest backend/tests

lint:
	ruff check backend

backend:
	python -m uvicorn nirv.api.main:app --app-dir backend --reload --port 8000

dev: backend

frontend:
	cd frontend && npm run dev

docker-up:
	docker compose up --build

docker-down:
	docker compose down

migrate:
	alembic -c backend/alembic.ini upgrade head
