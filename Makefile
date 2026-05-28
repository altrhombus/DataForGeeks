.PHONY: test lint typecheck check

test:
	uv run pytest

lint:
	uv run ruff check .

typecheck:
	uv run pyright

check: lint typecheck test
