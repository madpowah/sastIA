# SAST IA — Automated Security Analysis (Open Source)

> Static code analysis, Docker validation, and AI-powered detailed reports.

---

## Architecture

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
│  2. OpenCode Runner — calls SastIA subagents              │
│     │                                                     │
│     ├─ @SastIA_docker   → test environment                │
│     ├─ @SastIA_analyzer → security audit                  │
│     ├─ @SastIA_rapport  → final Markdown report           │
│     └─ POST callback    → /api/audits/{id}/callback       │
└──────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
./install.sh   # creates venvs, installs deps, creates admin user
./start.sh     # starts PostgreSQL (Docker), backend, worker, frontend
```

Then open **http://localhost:5173** and login with:
- **Email**: `admin@sastia.com`
- **Password**: `admin`

You will be prompted to change your password on first login.

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (optional, for PostgreSQL)

---

## Features

| Feature | Detail |
|---|---|
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
| `POST` | `/analyze` | `{audit_id, callback_url, repo_url?, model_id?, report_language}` |
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
         ├─ @SastIA_docker     → build & start test container
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

---

## License

MIT
