# SAST IA — Automated Security Analysis

**v0.2** — *VulnHunter pipeline + real Docker validation*

> AI-powered static analysis with adversarial verification and active Docker exploitation.

---

## Architecture v0.2

```
┌──────────────────────────────────────────────────────────┐
│                    Browser (User)                         │
│              React + Tailwind CSS + Vite                  │
└────────────────────┬─────────────────────────────────────┘
                     │  HTTP (port 3000)
                     ▼
┌──────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                       │
│  port 8000                                                │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐              │
│  │ Auth     │ │ Audits   │ │ Reports     │              │
│  │ JWT/bcrypt│ │ CRUD     │ │ Markdown/PDF│              │
│  └──────────┘ └──────────┘ └─────────────┘              │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ SQLAlchemy + SQLite (dev) / PostgreSQL (prod)        │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────┬─────────────────────────────────────┘
                     │  POST /analyze (port 9000)
                     ▼
┌──────────────────────────────────────────────────────────┐
│              Analysis Worker (FastAPI)                     │
│  port 9000                                                │
│                                                           │
│  1. Code Fetcher — git clone / download upload            │
│  2. OpenCode Runner — pipeline VulnHunter                 │
│     │                                                     │
│     ├─ Phase 1: Recon (input inventory, sinks, partitions)│
│     ├─ Phase 2: Hunt (trace inputs → sinks, candidates)   │
│     ├─ Phase 2b: Adversarial Verify (try to refute)       │
│     ├─ Phase 3: Reproduce + Fix + Sweep (PoC + sweep)    │
│     ├─ (optional) Docker Build + Real Exploit Validation │
│     └─ Report (VULN-NNN format + JSON)                   │
│                                                           │
│  3. Worker sends callback to backend                      │
└──────────────────────────────────────────────────────────┘
```

---

## What's new in v0.2

### VulnHunter pipeline integration
The old SAST pipeline (OWASP Top 10 checklist) has been replaced by the **VulnHunter methodology** — a rigorous multi-phase audit adapted from [vulnhunt](https://github.com/anomalyco/vulnhunt):

- **Phase 1 — Recon**: Complete input inventory, sink enumeration, call graph mapping, subgraph partitioning, threat model
- **Phase 2 — Hunt**: Parallel trace agents per partition and vulnerability class (INJ/NAV/LOG), sink-driven audit
- **Phase 2b — Adversarial Verification**: Systematic attempt to refute each candidate finding (cross-subgraph defense search, severity calibration, downgrade discipline)
- **Phase 3 — Reproduce + Fix + Sweep**: Static PoCs, exploit tests, fix strategies, codebase-wide sweep for root cause variants
- **Phase 4 — Report**: Comprehensive README with summary table, resolved input inventory, code quality section

### Real Docker validation (not self-validation)
The Docker step no longer runs the IA's own PoC scripts. Instead:

| App type | Validation method | Evidence |
|---|---|---|
| **Web app** | `curl` with real payloads against `DOCKER_URL` | Response body/status shows exploitation or blocking |
| **C/C++ library** | Compile harness with `-fsanitize=address`, execute with malicious data | AddressSanitizer crash report or clean exit |
| **CLI tool** | Execute binary with crafted arguments | Crash, data leak, or proper rejection |
| **API** | Crafted HTTP requests with injected payloads | Data exfiltration, error disclosure, or correct validation |

Each finding gets: **PASS** (exploit confirmed), **FAIL** (defense held), or **NOT-TESTED**.

### Report format
- Findings numbered **VULN-NNN** (one per sink location)
- CWE identifiers for every finding
- Summary table with severity > Docker validation > status
- Detailed findings with data flow, root cause, code snippet
- Resolved input inventory (completeness artifact)
- Code quality / defense in depth section
- PoC and exploit test files downloadable via ZIP

---

## Quick Start

```bash
./install.sh   # creates venvs, installs deps, creates admin user
./start.sh     # starts PostgreSQL (Docker), backend, worker, frontend (dev)

<<<<<<< HEAD
# Or in production:
=======
# Or production:
>>>>>>> fa71c93 (v0.2: VulnHunter pipeline + real Docker validation)
docker compose up -d db backend frontend
```

Then open the app in your browser:
- **Email**: `admin@sastia.com`
<<<<<<< HEAD
- **Password**: `admin`

> **Ports**: By default, the frontend runs on port **3000** and the backend on **8000** (`docker compose up`).
> In dev mode (`./start.sh`), the Vite frontend runs on port **5173**.

You will be prompted to change your password on first login.

---

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (optional, for PostgreSQL)

### System Dependencies (PDF Export)

PDF generation uses **WeasyPrint**, which requires system libraries for font rendering:

```bash
# Debian / Ubuntu
sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0
```

These are installed automatically by `install.sh` when `sudo` is available.
=======
- **Password**: `admin123`
>>>>>>> fa71c93 (v0.2: VulnHunter pipeline + real Docker validation)

---

## Configuration — `backend/.env`

<<<<<<< HEAD
Generated by `./install.sh`. Any modification requires a backend restart.
=======
Généré par `./install.sh`.
>>>>>>> fa71c93 (v0.2: VulnHunter pipeline + real Docker validation)

| Variable | Default | Description |
|---|---|---|
<<<<<<< HEAD
| `SECRET_KEY` | `(random at install)` | **JWT key** — random 48-character string. **Critical.** The backend refuses to start if absent. |
| `DATABASE_URL` | `sqlite:///./sastia.db` | Database connection URL (SQLite or PostgreSQL). |
| `ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT token validity (24h). |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed browser request URLs (comma-separated). |
| `UPLOAD_DIR` | `./uploads` | Uploaded file storage directory. |
| `WORKER_URL` | `http://localhost:9000` | Analysis worker URL. |
| `CODE_DOWNLOAD_BASE_URL` | `http://localhost:8000` | Public backend URL for worker callback. |

---

### Server Installation

```bash
git clone https://github.com/madpowah/sastIA.git
cd sastIA
chmod +x install.sh start.sh
./install.sh
```

#### 1. PostgreSQL port already in use (port 5432 occupied)

```bash
# backend/.env
POSTGRES_PORT=5433
DATABASE_URL=postgresql://sastia:***@localhost:5433/sastia
```

#### 2. CORS — Origin not allowed

Add your domain URL to `CORS_ORIGINS`:

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000,http://YOUR-DOMAIN.com
```

#### 3. JWT Key (SECRET_KEY)

Auto-generated by `install.sh`. To generate one manually:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the result into `backend/.env`:

```env
SECRET_KEY=your-generated-key-here
```

---

### PostgreSQL (optional)

By default the application uses SQLite. For PostgreSQL:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sastia
POSTGRES_PASSWORD=my-password
POSTGRES_DB=sastia
DATABASE_URL=postgresql://sastia:***@localhost:5432/sastia
```

With Docker Compose:
```bash
POSTGRES_PASSWORD=my-password docker compose up -d
=======
| `SECRET_KEY` | (aléatoire à l'install) | **Clé JWT** — chaîne aléatoire. **Critique.** |
| `DATABASE_URL` | `sqlite:///./sastia.db` | SQLite ou PostgreSQL |
| `CORS_ORIGINS` | `http://localhost:3000,...` | URLs autorisées pour CORS |
| `WORKER_URL` | `http://localhost:9000` | URL du worker |
| `CODE_DOWNLOAD_BASE_URL` | `http://localhost:8000` | URL publique du backend |

Les IP privées Docker (`172.x.x.x`, `192.168.x.x`, `10.x.x.x`) sont automatiquement acceptées par le middleware CORS.

---

## API Changes (v0.2)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/reports/{id}/zip` | Download full report ZIP (README + PoCs + exploit tests) |
| `GET` | `/api/audits/{id}/artifacts/{path}` | Serve PoC / exploit test files |

---

## Project Structure (v0.2)

```
sastIA/
├── .opencode/
│   ├── agents/                    # SAST subagents
│   │   ├── sastia_manager.md      # VulnHunter orchestrator
│   │   ├── sastia_analyzer.md     # Phase 1-3 + Docker validation
│   │   ├── sastia_rapport.md      # VULN-NNN report + JSON
│   │   └── sastia_docker.md       # Docker build & cleanup
│   └── skills/vulnhunt/           # VulnHunter phase files
│       ├── SKILL.md               # Adapted (no Opus check, static-only)
│       └── phases/
│           ├── phase1_recon.md
│           ├── phase2_hunt.md
│           ├── phase2_shared.md
│           ├── phase2_class_inj.md
│           ├── phase2_class_nav.md
│           ├── phase2_class_log.md
│           ├── phase2b_verify.md
│           ├── phase3_reproduce_test.md
│           ├── phase3c_fixes.md
│           ├── phase3d_sweep.md
│           └── phase4_report.md
├── backend/
│   ├── app/routers/
│   │   ├── audits.py              # + artifacts endpoint
│   │   └── reports.py             # + ZIP download
│   └── app/services/
│       └── report.py              # PDF simplify + ZIP creation
├── frontend/
│   └── src/pages/
│       └── Report.tsx             # Modal viewer, ZIP button, MD toggle
└── worker/
    ├── main.py                    # + skills sync, artifact collect
    └── opencode_runner.py         # VulnHunter prompt, worker callback
>>>>>>> fa71c93 (v0.2: VulnHunter pipeline + real Docker validation)
```

---

<<<<<<< HEAD
### Default AI Model

```env
OPENCODE_MODEL=opencode/deepseek-v4-flash-free
```

Or in `worker/opencode_runner.py`.

=======
>>>>>>> fa71c93 (v0.2: VulnHunter pipeline + real Docker validation)
## Features

| Feature | Detail |
|---|---|
<<<<<<< HEAD
| **Login / Auth** | JWT + bcrypt, password change on first login |
| **Dashboard** | Global stats, severity counters, recent audits |
| **New Audit** | Upload code (ZIP) or Git repository URL |
| **Code Analysis** | SAST agents (OWASP Top 10, CVSS, RCE, injections...) |
| **Docker Validation** | Build + exploit testing in isolated container |
| **Markdown Reports** | Full report with vulnerability details table |
| **PDF Export** | Formatted PDF download (WeasyPrint) |
| **Report Language** | Choose English or French for each audit |
| **Model Selection** | Choose AI model per audit (admin-configured) |
| **Async Pipeline** | Backend → Worker → Agents → Callback |
| **Real-time Polling** | Frontend polls status every 10 seconds |
| **Admin Panel** | User management, model management, audit overview |
| **i18n** | English / French interface, persisted in localStorage |

---

## Admin Guide

### Default admin credentials

Created by `install.sh`:

```
Email:    admin@sastia.com
Password: admin (must change on first login)
```

### User management (Admin > Users)

- Create users with email, name, password, admin role toggle
- Toggle active/inactive status
- Promote/demote admin role
- Reset user passwords
- Delete users

### Model management (Admin > Models)

1. Configure opencode with your API keys: `opencode connect`
2. Click **"Refresh models"** — runs `opencode models` and imports all available models
3. Toggle models **Enabled** to make them available for users
4. Users see only enabled models when creating an audit

---

## API

### Authentication

| Method | Endpoint | Body | Response |
|---|---|---|---|
| `POST` | `/api/auth/login` | `{email, password}` | `{access_token, user}` |
| `GET` | `/api/auth/me` | — | `{id, email, full_name, ...}` |
| `POST` | `/api/auth/change-password` | `{current_password, new_password}` | `{status}` |

### Audits

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/audits/dashboard` | User stats + last 10 audits |
| `GET` | `/api/audits/` | List user audits |
| `POST` | `/api/audits/` | Create audit (multipart) |
| `GET` | `/api/audits/{id}` | Audit detail |
| `POST` | `/api/audits/{id}/start` | Start analysis → dispatches to worker |
| `GET` | `/api/audits/{id}/download` | Download uploaded code |
| `DELETE` | `/api/audits/{id}` | Delete audit |

### Callback (worker → backend)

| Method | Endpoint | Body |
|---|---|---|
| `POST` | `/api/audits/{id}/callback` | `{report_markdown, vulnerabilities?, error?}` |

### Reports

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/reports/{id}` | Report markdown |
| `GET` | `/api/reports/{id}/pdf` | Download PDF |

### Admin

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/dashboard` | Admin stats |
| `GET` | `/api/admin/users` | List users (paginated) |
| `POST` | `/api/admin/users` | Create user |
| `PATCH` | `/api/admin/users/{id}` | Toggle active/admin |
| `DELETE` | `/api/admin/users/{id}` | Delete user |
| `POST` | `/api/admin/users/{id}/reset-password` | Reset user password |
| `GET` | `/api/admin/audits` | List all audits |
| `GET` | `/api/admin/audits/{id}` | Audit detail + report |
| `GET` | `/api/admin/audits/{id}/log` | Worker logs |
| `POST` | `/api/admin/audits/{id}/retry` | Retry failed audit |
| `GET` | `/api/admin/models/refresh` | Run `opencode models`, import all |
| `GET` | `/api/admin/models` | List all stored models |
| `POST` | `/api/admin/models/toggle` | Enable/disable a model |
| `GET` | `/api/admin/public/models` | List enabled models (public) |

### Worker

| Method | Endpoint | Body |
|---|---|---|
| `POST` | `/analyze` | `{audit_id, callback_url, repo_url?, code_path?, model_id?, report_language, docker_analysis}` |
| `GET` | `/health` | Health check |

---

## Customizing

### Changing the default AI model

Edit `worker/opencode_runner.py`:
```python
DEFAULT_MODEL = "opencode/deepseek-v4-flash-free"
```

Or set the `OPENCODE_MODEL` environment variable.

### Adding AI providers

```bash
opencode connect   # interactive provider setup
opencode models    # verify models are available
```

Then in the admin panel: **Admin > Models > Refresh models**, toggle the ones you want.

---

## Project Structure

```
sastIA/
├── backend/                    # REST API
│   ├── app/
│   │   ├── main.py             # FastAPI entry point
│   │   ├── config.py           # Settings (.env)
│   │   ├── database.py         # SQLAlchemy engine
│   │   ├── models.py           # User, Audit, AvailableModel
│   │   ├── schemas.py          # Pydantic models
│   │   ├── auth.py             # JWT + bcrypt
│   │   ├── routers/
│   │   │   ├── auth.py         # Login, Me, ChangePassword
│   │   │   ├── audits.py       # CRUD, callback, dispatch
│   │   │   ├── reports.py      # Report + PDF
│   │   │   └── admin.py        # Admin: users, audits, models
│   │   └── services/
│   │       ├── analysis.py     # Legacy worker payload
│   │       └── report.py       # PDF generation (WeasyPrint)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # React app
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── ChangePassword.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── NewAudit.tsx
│   │   │   ├── AuditsList.tsx
│   │   │   ├── AuditDetail.tsx
│   │   │   ├── Report.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── admin/          # Admin pages
│   │   ├── components/         # UI components
│   │   ├── context/            # AuthContext, LanguageContext
│   │   └── i18n/               # EN/FR translations
│   ├── package.json
│   └── Dockerfile
│
├── worker/                     # Analysis worker
│   ├── main.py                 # POST /analyze, log viewer
│   ├── code_fetcher.py         # Git clone / upload download
│   ├── opencode_runner.py      # Runs opencode agents
│   ├── Dockerfile
│   └── requirements.txt
│
├── .opencode/agents/           # SAST subagents
│   ├── sastia_manager.md       # Orchestrator
│   ├── sastia_docker.md        # Docker test env
│   ├── sastia_analyzer.md      # Security audit
│   └── sastia_rapport.md       # Report generation
│
├── install.sh                  # One-command setup
├── start.sh                    # One-command launch
├── docker-compose.yml
└── README.md
```

---

## Worker Workflow

```
User clicks "Launch" → POST /api/audits/{id}/start
         │
         ▼
Backend sets status=analyzing_code
         │
         ▼
HTTP POST → Worker :9000/analyze
         │
         ├── repo_url ? git clone --depth 1
         └── upload ? GET /api/audits/{id}/download + extract
         │
         ▼
Worker runs: opencode run --model X --dir <code> ...
         │
         ├─ (optional) @SastIA_docker → build & start test container
         ├─ @SastIA_analyzer   → OWASP + RCE + injection audit
         ├─ @SastIA_rapport    → generate final report
         │
         ▼
POST callback → /api/audits/{id}/callback
         │
         ├─ report_markdown stored in DB
         ├─ vulnerability counts parsed
         └─ status → "completed"
```
=======
| **VulnHunter pipeline** | 4-phase audit: Recon → Hunt → Verify → Report |
| **Adversarial verification** | Systematic attempt to refute each finding |
| **Docker validation** | Real exploit testing (curl/ASAN/exec) — not self-validation |
| **VULN-NNN format** | One finding per sink location with CWE |
| **Report ZIP** | Download full report with PoCs + exploit tests |
| **PoC/exploit modal** | In-page viewer with raw/rendered toggle |
| **Model-compatible** | Works with ALL AI models, no Opus requirement |
>>>>>>> fa71c93 (v0.2: VulnHunter pipeline + real Docker validation)

---

## License

MIT
