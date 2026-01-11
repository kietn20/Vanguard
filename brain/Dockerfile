# AI Agent system container
FROM python:3.12-slim

# Install poetry
RUN pip install --no-cache-dir poetry==2.2.1

WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 vanguard && \
    chown -R vanguard:vanguard /app

USER vanguard

# Run the agent consumer
CMD ["python", "consumer.py"]
