.PHONY: help dev test migrate seed eval smoke down

PYTHON ?= uv run
API_DIR = api

help:
	@echo "Available commands:"
	@echo "  make dev      - Start redis, test-db, and run the FastAPI development server"
	@echo "  make test     - Run all automated tests (no external API calls)"
	@echo "  make migrate  - Run database migrations"
	@echo "  make seed     - Seed database with initial grades and testers"
	@echo "  make eval     - Run Amharic quality evaluations with real models"
	@echo "  make smoke    - Run smoke tests against configured providers"
	@echo "  make down     - Stop all background docker services"

dev:
	docker compose up -d redis test-db
	cd $(API_DIR) && uv run uvicorn app.main:app --reload --port 8000 --host 0.0.0.0

test:
	cd $(API_DIR) && uv run pytest

migrate:
	cd $(API_DIR) && uv run alembic upgrade head

seed:
	cd $(API_DIR) && uv run python scripts/seed_testers.py

eval:
	cd $(API_DIR) && uv run python evals/run_eval.py

smoke:
	cd $(API_DIR) && uv run python scripts/smoke_check.py

down:
	docker compose down
