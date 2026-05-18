#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

cleanup() {
    echo ""
    echo "=== Stopping all services ==="
    kill $BACKEND_PID $FRONTEND_PID $WORKER_PID 2>/dev/null || true
    if [ -n "${POSTGRES_CONTAINER:-}" ]; then
        docker stop "$POSTGRES_CONTAINER" 2>/dev/null || true
    fi
    wait
    echo "Done."
}
trap cleanup EXIT INT TERM

echo "=== SAST IA — Start ==="
echo ""

# ── PostgreSQL ─────────────────────────────────────────
POSTGRES_CONTAINER=""
if command -v docker &>/dev/null; then
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'sastia-db'; then
        POSTGRES_CONTAINER="sastia-db"
        echo "[✓] PostgreSQL already running (sastia-db)"
    else
        echo "[…] Starting PostgreSQL via Docker..."
        POSTGRES_CONTAINER=$(docker run -d \
            --name sastia-db \
            -e POSTGRES_USER=sastia \
            -e POSTGRES_PASSWORD=sastia \
            -e POSTGRES_DB=sastia \
            -p 5432:5432 \
            postgres:16-alpine 2>/dev/null || true)
        if [ -n "$POSTGRES_CONTAINER" ]; then
            echo "[✓] PostgreSQL started (container: sastia-db)"
            echo "  Waiting for PostgreSQL to be ready..."
            for i in $(seq 1 15); do
                if docker exec sastia-db pg_isready -U sastia &>/dev/null; then
                    echo "  → Ready after ${i}s"
                    break
                fi
                sleep 1
            done
        else
            echo "[!] PostgreSQL container already exists, reusing it"
            docker start sastia-db 2>/dev/null || true
            POSTGRES_CONTAINER="sastia-db"
        fi
    fi
fi

# ── Backend ────────────────────────────────────────────
echo ""
echo "[…] Starting Backend (FastAPI) on :8000"
cd backend
../venv/bin/uvicorn app.main:app --reload --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!
cd "$ROOT_DIR"
echo "[✓] Backend PID $BACKEND_PID"

# ── Worker ─────────────────────────────────────────────
echo "[…] Starting Worker (FastAPI) on :9000"
cd worker
../worker-venv/bin/uvicorn main:app --reload --port 9000 --host 0.0.0.0 &
WORKER_PID=$!
cd "$ROOT_DIR"
echo "[✓] Worker PID $WORKER_PID"

# ── Frontend ───────────────────────────────────────────
echo "[…] Starting Frontend (Vite) on :5173"
cd frontend
npx vite --host 0.0.0.0 &
FRONTEND_PID=$!
cd "$ROOT_DIR"
echo "[✓] Frontend PID $FRONTEND_PID"

echo ""
echo "============================================"
echo "  Frontend : http://localhost:5173"
echo "  Backend  : http://localhost:8000"
echo "  Worker   : http://localhost:9000"
echo "  DB       : postgresql://sastia:sastia@localhost:5432/sastia"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop all services."

wait
