#!/bin/sh
set -eu

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

BACKEND_PID=""
FRONTEND_PID=""
WORKER_PID=""
POSTGRES_CONTAINER=""

POSTGRES_USER="${POSTGRES_USER:-sastia}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(python3 -c "import secrets; print(secrets.token_urlsafe(24))" 2>/dev/null || openssl rand -hex 16)}"
POSTGRES_DB="${POSTGRES_DB:-sastia}"

cleanup() {
    echo ""
    echo "=== Stopping all services ==="
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    [ -n "$WORKER_PID" ] && kill "$WORKER_PID" 2>/dev/null || true
    if [ -n "$POSTGRES_CONTAINER" ]; then
        docker stop "$POSTGRES_CONTAINER" 2>/dev/null || true
    fi
    echo "Done."
}
trap cleanup EXIT INT TERM

echo "=== SAST IA -- Start ==="
echo ""

# -- PostgreSQL ------------------------------------------------------------
if command -v docker >/dev/null 2>&1; then
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'sastia-db'; then
        POSTGRES_CONTAINER="sastia-db"
        echo "[OK] PostgreSQL already running (sastia-db)"
    else
        echo "[..] Starting PostgreSQL via Docker..."
        POSTGRES_CONTAINER=$(docker run -d \
            --name sastia-db \
            -e POSTGRES_USER="${POSTGRES_USER}" \
            -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
            -e POSTGRES_DB="${POSTGRES_DB}" \
            -p 5432:5432 \
            postgres:16-alpine 2>/dev/null || true)
        if [ -n "$POSTGRES_CONTAINER" ]; then
            echo "[OK] PostgreSQL started (container: sastia-db)"
            echo "  Waiting for PostgreSQL to be ready..."
            i=0
            while [ $i -lt 15 ]; do
                if docker exec sastia-db pg_isready -U "${POSTGRES_USER}" >/dev/null 2>&1; then
                    echo "  -> Ready after $((i+1))s"
                    break
                fi
                i=$((i+1))
                sleep 1
            done
        else
            echo "[--] PostgreSQL container may already exist, reusing it"
            docker start sastia-db 2>/dev/null || true
            POSTGRES_CONTAINER="sastia-db"
        fi
    fi
fi

# -- Backend ---------------------------------------------------------------
echo ""
echo "[..] Starting Backend (FastAPI) on :8000"
cd backend
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}" \
../venv/bin/uvicorn app.main:app --reload --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!
cd "$ROOT_DIR"
echo "[OK] Backend PID $BACKEND_PID"

# -- Worker ----------------------------------------------------------------
echo "[..] Starting Worker (FastAPI) on :9000"
cd worker
../worker-venv/bin/uvicorn main:app --reload --port 9000 --host 0.0.0.0 &
WORKER_PID=$!
cd "$ROOT_DIR"
echo "[OK] Worker PID $WORKER_PID"

# -- Frontend --------------------------------------------------------------
echo "[..] Starting Frontend (Vite) on :5173"
cd frontend
npx vite --host 0.0.0.0 &
FRONTEND_PID=$!
cd "$ROOT_DIR"
echo "[OK] Frontend PID $FRONTEND_PID"

echo ""
echo "============================================"
echo "  Frontend : http://localhost:5173"
echo "  Backend  : http://localhost:8000"
echo "  Worker   : http://localhost:9000"
echo "  DB       : postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop all services."

wait
