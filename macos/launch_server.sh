#!/usr/bin/env bash
# Simple macOS launcher for the Sailing Logbook Django app
# - Ensures virtualenv
# - Installs requirements (idempotent)
# - Applies migrations
# - Opens default browser on http://127.0.0.1:8000
# - Starts Django dev server (Ctrl+C to stop)

set -euo pipefail
cd "$(dirname "$0")/.."

PORT=${PORT:-8000}
HOST=127.0.0.1
VENV=".venv"

echo "[Sailing Logbook] Using Python: $(python3 -V || true)"

if [ ! -d "$VENV" ]; then
  echo "[Sailing Logbook] Creating virtualenv at $VENV"
  python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"
python -m pip install --upgrade pip >/dev/null
echo "[Sailing Logbook] Installing dependencies (if needed)…"
pip install -r requirements.txt >/dev/null

echo "[Sailing Logbook] Applying migrations…"
python manage.py migrate --noinput

URL="http://$HOST:$PORT/"
echo "[Sailing Logbook] Opening $URL"
open "$URL" || true

echo "[Sailing Logbook] Starting server on $HOST:$PORT (Ctrl+C to stop)"
exec python manage.py runserver "$HOST:$PORT"
