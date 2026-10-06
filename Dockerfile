FROM ghcr.io/astral-sh/uv:0.12.11 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_CACHE_DIR=/tmp/uv-cache
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN useradd --uid 10001 --create-home learning \
    && chown -R learning:learning /app /tmp/uv-cache
USER learning
EXPOSE 8000
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync python -m app.db.seed && uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
