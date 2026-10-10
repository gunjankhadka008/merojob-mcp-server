#!/usr/bin/env bash
# Starts the MeroJob backend server.
# Run with:  bash start.sh
set -e
cd "$(dirname "$0")"

if [ ! -d venv ] || [ ! -f .env ]; then
  echo "Not set up yet. Run this first:  bash setup.sh"
  exit 1
fi

# shellcheck disable=SC1091
source venv/bin/activate

# Load MEROJOB_API_KEY from .env
set -a
# shellcheck disable=SC1091
source .env
set +a

if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port 8000 is already in use. The server is probably already running"
  echo "in another terminal. Use that one, or stop it with Ctrl+C first."
  exit 1
fi

echo "Starting MeroJob server on http://127.0.0.1:8000"
echo "Leave this window open while you use Claude. Press Ctrl+C to stop."
exec uvicorn main:app --host 127.0.0.1 --port 8000
