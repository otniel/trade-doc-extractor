.PHONY: install dev test lint run eval lock

install:            ## runtime deps only
	uv sync --no-dev

dev:                ## runtime + dev deps
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check src tests eval

run:                ## make run FILE=documents/trade_confirmation_001.pdf
	uv run python -m src.cli $(FILE)

eval:
	uv run python -m eval.run_eval

lock:               ## refresh lockfile + export pinned requirements for pip users
	uv lock
	uv export --no-hashes --no-dev -o requirements.txt
	uv export --no-hashes --only-dev -o requirements-dev.txt
