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

# Optional: install libpq-dev + python3-dev for psycopg2
if command -v sudo >/dev/null 2>&1 && apt-get --version >/dev/null 2>&1; then
    MISSING_DEV=""
    dpkg -l libpq-dev >/dev/null 2>&1 || MISSING_DEV="libpq-dev"
    dpkg -l python3-dev >/dev/null 2>&1 || MISSING_DEV="$MISSING_DEV python3-dev"
    if [ -n "$MISSING_DEV" ]; then
        echo "  -> Installing$MISSING_DEV (for PostgreSQL driver)..."
        sudo apt-get install -y -qq $MISSING_DEV 2>/dev/null || echo "  -> (skipped, SQLite will be used)"
    else
        echo "  -> build dependencies already installed"
    fi
fi

# WeasyPrint system libraries (PDF generation)
if command -v sudo >/dev/null 2>&1 && apt-get --version >/dev/null 2>&1; then
    MISSING_WP=""
    dpkg -l libpango-1.0-0 >/dev/null 2>&1 || MISSING_WP="$MISSING_WP libpango-1.0-0"
    dpkg -l libpangocairo-1.0-0 >/dev/null 2>&1 || MISSING_WP="$MISSING_WP libpangocairo-1.0-0"
    dpkg -l libgdk-pixbuf-2.0-0 >/dev/null 2>&1 || MISSING_WP="$MISSING_WP libgdk-pixbuf-2.0-0"
    if [ -n "$MISSING_WP" ]; then
        echo "  -> Installing$MISSING_WP (for PDF generation)..."
        sudo apt-get install -y -qq $MISSING_WP 2>/dev/null || echo "  -> (skipped, PDF disabled)"
    else
        echo "  -> WeasyPrint libraries already installed"
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
    RANDOM_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))" 2>/dev/null || openssl rand -hex 32 2>/dev/null || echo "change-this-to-a-long-random-string-in-production")
    cat > backend/.env << ENVEOF
DATABASE_URL=sqlite:///./sastia.db
SECRET_KEY=${RANDOM_SECRET}
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

# ── 7. Default admin user ──────────────────────────────
echo "[7/6] Creating default admin user"
cd backend
cat > /tmp/create_admin.py << 'PYEOF'
import sqlite3, uuid, bcrypt
from datetime import datetime, timezone

db_path = 'sastia.db'
conn = sqlite3.connect(db_path)

conn.execute('''CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    company TEXT,
    is_active INTEGER DEFAULT 1,
    is_admin INTEGER DEFAULT 0,
    must_change_password INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)''')

cur = conn.execute("SELECT id FROM users WHERE email = 'admin@sastia.com'")
if not cur.fetchone():
    pw_hash = bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode()
    uid = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO users (id, email, password_hash, full_name, is_active, is_admin, must_change_password, created_at) VALUES (?, ?, ?, ?, 1, 1, 1, ?)",
        (uid, 'admin@sastia.com', pw_hash, 'Administrator', now)
    )
    conn.commit()
    print('  -> Created admin@sastia.com / admin (must change password)')
else:
    print('  -> admin@sastia.com already exists')
conn.close()
PYEOF
../venv/bin/python /tmp/create_admin.py 2>&1 || echo "  -> (skipped)"
rm /tmp/create_admin.py
cd "$ROOT_DIR"

echo ""
echo "=== Installation complete ==="
echo "Run ./start.sh to launch all services."
