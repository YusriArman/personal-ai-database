.PHONY: setup test lint eval eval-live experiment api ui

setup:
	cd backend && uv sync
	cd frontend && npm install

test:
	cd backend && uv run pytest -q
	cd frontend && npm test

lint:
	cd backend && uv run ruff check .
	cd frontend && npx tsc --noEmit

eval:            ## deterministic, no model needed
	cd backend && uv run python -m app.evaluate deterministic

eval-live:       ## needs Ollama running; set LNC_PROFILE=m4 or ryzen
	cd backend && uv run python -m app.evaluate live --runs 3

experiment:
	cd backend && uv run python ../experiments/note_classifier/train.py

api:
	cd backend && uv run uvicorn app.api.main:app --reload --port 8000

ui:
	cd frontend && npm run dev
