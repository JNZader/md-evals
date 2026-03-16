#!/usr/bin/env bash
# Startup script for md-evals server container.
# Runs Alembic migrations then starts uvicorn.
set -euo pipefail

echo "==> Running database migrations..."
python -m alembic upgrade head

echo "==> Starting uvicorn server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info
