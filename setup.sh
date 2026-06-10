#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/back_end_api"
FRONTEND_DIR="$ROOT_DIR/fe_react_UI"

log() {
  printf "\n[setup] %s\n" "$1"
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf "[setup] Missing command: %s\n" "$1" >&2
    exit 1
  fi
}

log "Checking required tools"
need_cmd python
need_cmd node
need_cmd npm

log "Setting up backend virtual environment"
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
  python -m venv venv
fi

if [ -x "venv/Scripts/python.exe" ]; then
  PYTHON_BIN="venv/Scripts/python.exe"
  PIP_BIN="venv/Scripts/pip.exe"
  ALEMBIC_BIN="venv/Scripts/alembic.exe"
else
  PYTHON_BIN="venv/bin/python"
  PIP_BIN="venv/bin/pip"
  ALEMBIC_BIN="venv/bin/alembic"
fi

log "Installing backend dependencies"
"$PYTHON_BIN" -m pip install --upgrade pip
"$PIP_BIN" install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  log "Creating backend .env from .env.example"
  cp .env.example .env
  printf "[setup] Please edit back_end_api/.env before running the app.\n"
fi

log "Installing frontend dependencies"
cd "$FRONTEND_DIR"
npm install

if [ ! -f ".env" ]; then
  log "Creating frontend .env"
  printf "VITE_API_BASE_URL=http://localhost:8000\n" > .env
fi

log "Running basic checks"
cd "$BACKEND_DIR"
"$PYTHON_BIN" -m compileall app alembic

cd "$FRONTEND_DIR"
npm run build

cat <<'NEXT'

[setup] Done.

Next steps:
1. Edit back_end_api/.env with your MySQL, JWT, AI, Google OAuth and SePay values.
2. Create your MySQL database.
3. Run migrations:
   cd back_end_api
   venv/Scripts/alembic.exe upgrade head   # Git Bash on Windows
   # or venv/bin/alembic upgrade head      # Linux/macOS/WSL

4. Start backend:
   venv/Scripts/uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000

5. Start frontend in another terminal:
   cd fe_react_UI
   npm run dev -- --host 127.0.0.1

NEXT
