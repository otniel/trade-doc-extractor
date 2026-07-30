.PHONY: install dev test lint run eval lock

install:            ## runtime deps only
	uv sync --no-dev

dev:                ## runtime + dev deps
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check src tests

run:                ## make run FILE=corpus/trade_confirmation_001.pdf
	PYTHONPATH=src uv run python -m cli $(FILE)

eval:
	PYTHONPATH=src uv run python eval/run_eval.py

lock:               ## refresh lockfile + export pinned requirements for pip users
	uv lock
	uv export --no-hashes --no-dev -o requirements.txt
	uv export --no-hashes --only-dev -o requirements-dev.txt
