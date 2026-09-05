.PHONY: help install dev test lint typecheck data benchmark clean

help:
	@echo "ShadowLedger Build Automation"
	@echo "----------------------------"
	@echo "make install    : Install Python backend and Node frontend dependencies"
	@echo "make dev        : Run FastAPI backend (:8000) and Next.js frontend (:3000)"
	@echo "make test       : Run automated pytest backend test suite"
	@echo "make lint       : Run ruff (Python) and eslint (TypeScript)"
	@echo "make typecheck  : Run mypy and tsc"
	@echo "make data       : Generate 10,000 synthetic multi-source records"
	@echo "make benchmark  : Run deterministic baseline benchmark against ground truth"
	@echo "make clean      : Remove temporary caches and generated logs"

install:
	python3 -m venv .venv || true
	./.venv/bin/pip install -e "./apps/api[dev]"
	cd apps/web && npm ci

dev:
	@echo "Starting ShadowLedger Backend and Frontend..."
	./.venv/bin/uvicorn apps.api.app.main:app --reload --port 8000 &
	npm --prefix apps/web run dev

test:
	./.venv/bin/pytest apps/api/tests -v

test-e2e:
	npm --prefix apps/web run test:e2e

lint:
	./.venv/bin/ruff check apps/api scripts
	npm --prefix apps/web run lint

typecheck:
	./.venv/bin/mypy apps/api
	npm --prefix apps/web run typecheck

data:
	./.venv/bin/python scripts/generate_dataset.py --rows 10000 --seed 42

benchmark:
	./.venv/bin/python scripts/run_benchmark.py --rows 10000 --seed 42

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache apps/web/.next apps/web/out
	find . -type d -name "__pycache__" -exec rm -rf {} +
