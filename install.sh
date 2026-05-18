#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "=== SAST IA — Installation ==="
echo ""

# ── 1. Backend venv ────────────────────────────────────
echo "[1/5] Backend — virtualenv + dependencies"
if [ ! -d venv ]; then
    python3 -m venv venv
fi
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r backend/requirements.txt

# ── 2. Worker venv ─────────────────────────────────────
echo "[2/5] Worker — virtualenv + dependencies"
if [ ! -d worker-venv ]; then
    python3 -m venv worker-venv
fi
./worker-venv/bin/pip install --quiet --upgrade pip
./worker-venv/bin/pip install --quiet -r worker/requirements.txt

# ── 3. Frontend ────────────────────────────────────────
echo "[3/5] Frontend — npm install"
cd frontend
npm install --silent
cd "$ROOT_DIR"

# ── 4. .env ────────────────────────────────────────────
echo "[4/5] Backend .env"
if [ ! -f backend/.env ]; then
    cat > backend/.env << 'ENVEOF'
DATABASE_URL=sqlite:///./sastia.db
SECRET_KEY=change-this-to-a-long-random-string-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
UPLOAD_DIR=./uploads
WORKER_URL=http://localhost:9000
CODE_DOWNLOAD_BASE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
ENVEOF
    echo "  → backend/.env created (SQLite, dev defaults)"
else
    echo "  → backend/.env already exists, skipped"
fi

# ── 5. PostgreSQL via Docker (optional) ─────────────────
echo "[5/5] PostgreSQL Docker image (pull only)"
if command -v docker &>/dev/null; then
    docker pull postgres:16-alpine --quiet 2>/dev/null || echo "  → (docker not available, SQLite will be used)"
else
    echo "  → (docker not found, SQLite will be used)"
fi

echo ""
echo "=== Installation complete ==="
echo "Run ./start.sh to launch all services."
