# Multi-stage build for FastAPI + Kafka consumer
FROM python:3.12-slim AS base

# Install poetry
RUN pip install --no-cache-dir poetry==2.2.1

WORKDIR /app

# Copy poetry files
COPY pyproject.toml ./

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 vanguard && \
    chown -R vanguard:vanguard /app

USER vanguard

# Expose both API and metrics ports
EXPOSE 8000 8001

# Health check for API
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command (can be overridden)
CMD ["python", "run_api.py"]
