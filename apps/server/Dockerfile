# ============================================================
# Stage 1: Builder — install dependencies
# ============================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system deps for building cryptography / asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy md-evals core (needed as dependency)
COPY pyproject.toml README.md /build/
COPY md_evals/ /build/md_evals/

# Copy server requirements and install
COPY apps/server/requirements.txt /build/apps/server/requirements.txt
RUN pip install --no-cache-dir --prefix=/install \
    -r /build/apps/server/requirements.txt \
    -e /build/

# ============================================================
# Stage 2: Runtime — slim image
# ============================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install only runtime libs (libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash appuser

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Copy md-evals core
COPY md_evals/ /app/md_evals/
COPY pyproject.toml /app/pyproject.toml

# Copy server code
COPY apps/server/app/ /app/app/

# Switch to non-root
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
