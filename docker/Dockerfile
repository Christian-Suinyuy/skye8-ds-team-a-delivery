FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_HTTP_TIMEOUT=300

COPY pyproject.toml uv.lock ./
COPY src ./src
COPY data ./data
COPY models ./models
COPY mlflow.db ./mlflow.db

RUN uv sync --frozen --no-dev


FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/data /app/data
COPY --from=builder /app/models /app/models
COPY --from=builder /app/mlflow.db /app/mlflow.db

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser

# SQLite needs the application directory and database file to be writable.
RUN chown appuser:appuser /app
RUN chown appuser:appuser /app/mlflow.db

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-8000}"]