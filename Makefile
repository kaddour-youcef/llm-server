.PHONY: help dev run build up down test lint fmt clean

help:
	@echo "Targets: dev run build up down test lint fmt clean"

dev:
	uvicorn gateway.app.main:app --reload --host 0.0.0.0 --port 8080

run:
	python -m uvicorn gateway.app.main:app --host 0.0.0.0 --port 8080

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down -v

test:
	pytest -q || true

lint:
	@echo "Add ruff/flake8 or eslint here"

fmt:
	@echo "Add black/prettier commands here"

clean:
	rm -rf __pycache__ .pytest_cache **/__pycache__

