#!/usr/bin/env bash
# ============================================================
# EatWise Backend - macOS / Linux launcher
# Usage: chmod +x run_mac.sh && ./run_mac.sh
# ============================================================
set -e

cd "$(dirname "$0")"

# Verify Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] Python 3 is not installed."
  echo "Install from https://python.org or: brew install python@3.11"
  exit 1
fi

# Create venv
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate
# shellcheck disable=SC1091
source venv/bin/activate

# Install deps if missing
if ! python -c "import fastapi" 2>/dev/null; then
  echo "Installing dependencies..."
  python -m pip install --upgrade pip
  pip install -r requirements.txt
fi

# Copy .env if missing
if [ ! -f ".env" ]; then
  cp .env.example .env
fi

# Init DB if missing
if [ ! -f "eatwise.db" ]; then
  echo "Initializing database with seed data..."
  python -m scripts.init_db
fi

echo
echo "============================================================"
echo " EatWise Backend is starting..."
echo " API docs:    http://127.0.0.1:8000/docs"
echo " Health:      http://127.0.0.1:8000/health"
echo " Press Ctrl+C to stop."
echo "============================================================"
echo

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
