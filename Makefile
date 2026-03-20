run:
	docker compose up -d --build

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
