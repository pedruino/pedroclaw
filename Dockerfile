FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy everything first
COPY pyproject.toml .
COPY src/ src/
COPY config/ config/
COPY tests/ tests/

# Install package with dev dependencies
RUN pip install --no-cache-dir ".[dev]"

EXPOSE 8000

CMD ["uvicorn", "pedroclaw.main:app", "--host", "0.0.0.0", "--port", "8000"]
