run:
	docker compose up -d --build

run-recreate:
	docker compose up -d --build --force-recreate

stop:
	docker compose down

test:
	docker compose run --rm \
		-v $(PWD)/tests:/app/tests \
		-v $(PWD)/src:/app/src \
		-e PYTHONPATH=/app/src \
		-e LLM_REVIEW_MODEL -e LLM_REVIEW_API_KEY -e LLM_REVIEW_API_BASE \
		-e LANGFUSE_ENABLED -e LANGFUSE_PUBLIC_KEY -e LANGFUSE_SECRET_KEY \
		-e LANGFUSE_HOST=http://langfuse-web:3000 -e LANGFUSE_OTEL_HOST=http://langfuse-web:3000 \
		worker python -m pytest $(if $(FILE),tests/$(FILE),tests/) -v -s --timeout=120

# Local development commands (requires uv installed locally)
install:
	uv pip install --no-cache-dir ".[dev]"

dev-deps:
	uv pip install --no-cache-dir pytest pytest-asyncio pytest-cov ruff mypy

test-local:
	uv run python -m pytest $(if $(FILE),tests/$(FILE),tests/) -v -s --timeout=120

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

type-check:
	uv run mypy src/
