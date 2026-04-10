FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/apps/api/.venv/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app/apps/api

COPY apps/api/pyproject.toml apps/api/uv.lock apps/api/README.md ./
RUN uv sync --frozen --no-dev

COPY apps/api/ ./
COPY fixtures/ /app/fixtures/
COPY packages/evaluation/ /app/packages/evaluation/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "eu_comply_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
