#!/usr/bin/env bash
# Start command for Render web service.
# Sets number of workers to 2 and binds to $PORT (set by Render).

set -e

cd "$(dirname "$0")"

echo "Starting gunicorn..."
exec gunicorn src.ui.app:app \
    --workers=1 \
    --bind=0.0.0.0:${PORT:-5000} \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info \
    --timeout=120