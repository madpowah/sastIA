#!/bin/sh
set -eu

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "=== SAST IA — Installation ==="
echo ""

# ── System dependencies ──────────────────────────────
echo "[0/6] System dependencies"
MISSING=""
for cmd in python3 node npm; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        MISSING="$MISSING $cmd"
    fi
done
if [ -n "$MISSING" ]; then
    echo "  -> Missing: $MISSING"
    echo "  Install them first (e.g. apt install python3 nodejs npm)"
    exit 1
fi
echo "  -> All found"

# Optional: install libpq-dev for psycopg2
if command -v sudo >/dev/null 2>&1 && apt-get --version >/dev/null 2>&1; then
    if ! dpkg -l libpq-dev >/dev/null 2>&1; then
        echo "  -> Installing libpq-dev (for PostgreSQL driver)..."
        sudo apt-get install -y -qq libpq-dev 2>/dev/null || echo "  -> (skipped, SQLite will be used)"
    else
        echo "  -> libpq-dev already installed"
    fi
fi

# ── 1. Backend venv ────────────────────────────────────
echo "[1/6] Backend — virtualenv + dependencies"
if [ ! -d venv ]; then
    python3 -m venv venv
fi
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r backend/requirements.txt

# ── 2. Worker venv ─────────────────────────────────────
echo "[2/6] Worker — virtualenv + dependencies"
if [ ! -d worker-venv ]; then
    python3 -m venv worker-venv
fi
./worker-venv/bin/pip install --quiet --upgrade pip
./worker-venv/bin/pip install --quiet -r worker/requirements.txt

# ── 3. Frontend ────────────────────────────────────────
echo "[3/6] Frontend — npm install"
cd frontend
npm install --silent
cd "$ROOT_DIR"

# ── 4. .env ────────────────────────────────────────────
echo "[4/6] Backend .env"
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
    echo "  -> backend/.env created (SQLite, dev defaults)"
else
    echo "  -> backend/.env already exists, skipped"
fi

mkdir -p backend/uploads

# ── 5. PostgreSQL driver (optional) ────────────────────
echo "[5/6] PostgreSQL driver (optional)"
if ./venv/bin/python -c "import psycopg2" 2>/dev/null; then
    echo "  -> psycopg2 already installed"
else
    echo "  -> Installing psycopg2-binary..."
    if ./venv/bin/pip install --quiet psycopg2-binary 2>/dev/null; then
        echo "  -> done"
    else
        echo "  -> skipped (SQLite will be used)"
    fi
fi

# ── 6. Pull Docker images (optional) ───────────────────
echo "[6/6] Docker images (optional)"
if command -v docker >/dev/null 2>&1; then
    docker pull postgres:16-alpine --quiet 2>/dev/null || true
fi

echo ""
echo "=== Installation complete ==="
echo "Run ./start.sh to launch all services."
