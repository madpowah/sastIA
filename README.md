# SAST IA — Automated Security Analysis

**v0.2** — *VulnHunter pipeline + real Docker validation*

> AI-powered static analysis with adversarial verification and active Docker exploitation.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           Browser (React + Tailwind)         │
└──────────────────┬──────────────────────────┘
                   │ HTTP
                   ▼
┌─────────────────────────────────────────────┐
│           Backend (FastAPI, port 8000)        │
│  Auth │ Audits │ Reports │ Admin             │
│  SQLite/PostgreSQL                            │
└──────────────────┬──────────────────────────┘
                   │ POST /analyze
                   ▼
┌─────────────────────────────────────────────┐
│         Analysis Worker (FastAPI, port 9000)  │
│                                              │
│  1. Code Fetcher                              │
│  2. VulnHunter Pipeline:                      │
│     Phase 1  Recon → Input inventory + sinks  │
│     Phase 2  Hunt  → Trace inputs → sinks     │
│     Phase 2b Verify → Adversarial refutation  │
│     Phase 3  Reproduce/Fix/Sweep              │
│     (opt.) Docker Build + Real Exploits       │
│     Phase 4  Report (VULN-NNN + JSON)         │
│  3. Callback → backend                        │
└──────────────────────────────────────────────┘
```

---

## Quick Start

```bash
./install.sh
./start.sh
```

Ouvre `http://localhost:5173` et connecte-toi avec :
- **Email** : `admin@sastia.com`
- **Mot de passe** : `admin123`

---

## What's new in v0.2

**VulnHunter pipeline** — L'ancien pipeline OWASP a été remplacé par la méthodologie [VulnHunter](https://github.com/capitalone/VulnHunter) : inventaire systématique des entrées, traçage entrée→sink, vérification adversariale, sweep codebase.

**Validation Docker réelle** — Le Docker ne se contente plus d'exécuter les scripts PoC de l'IA. Pour chaque type d'app :
- **Web app** : `curl` avec payloads réelles
- **Lib C** : compilation avec `-fsanitize=address`, exécution du vrai code
- **CLI** : lancement avec arguments malveillants

**Rapport VULN-NNN** — Findings numérotés avec CWE, table de synthèse, inventory résolu, section code quality.

**Téléchargement ZIP** — Rapport complet + PoCs + exploit tests dans une archive.

**Popup modale** — Visualisation des PoC/tests avec toggle raw/rendu MD.

**Compatible tous modèles** — Plus de restriction Opus.

---

## Configuration — `backend/.env`

| Variable | Défaut | Description |
|---|---|---|
| `SECRET_KEY` | (aléatoire à l'install) | Clé JWT |
| `DATABASE_URL` | `sqlite:///./sastia.db` | SQLite ou PostgreSQL |
| `CORS_ORIGINS` | `http://localhost:3000,...` | URLs autorisées |
| `WORKER_URL` | `http://localhost:9000` | URL du worker |
| `CODE_DOWNLOAD_BASE_URL` | `http://localhost:8000` | URL publique du backend |

Les IP privées Docker (`172.x`, `192.168.x`, `10.x`) sont automatiquement acceptées.

---

## API (v0.2 additions)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/reports/{id}/zip` | ZIP complet (README + PoCs + tests) |
| `GET` | `/api/audits/{id}/artifacts/{path}` | Fichiers PoC / exploit tests |

---

## Project Structure (v0.2)

```
sastIA/
├── .opencode/
│   ├── agents/                    # Subagents SAST
│   │   ├── sastia_manager.md      # Orchestrateur VulnHunter
│   │   ├── sastia_analyzer.md     # Phases 1-3 + validation Docker
│   │   ├── sastia_rapport.md      # Rapport VULN-NNN
│   │   └── sastia_docker.md       # Build & cleanup Docker
│   └── skills/vulnhunt/
│       ├── SKILL.md               # Adapté (static-only, tous modèles)
│       └── phases/                # 11 fichiers de phase VulnHunter
├── backend/
│   ├── app/routers/
│   │   ├── audits.py              # + artifacts endpoint
│   │   └── reports.py             # + ZIP download
│   └── app/services/
│       └── report.py              # PDF simplify + ZIP
├── frontend/
│   └── src/pages/
│       └── Report.tsx             # Modal viewer, ZIP, MD toggle
└── worker/
    ├── main.py                    # + skills sync, artifact collect
    └── opencode_runner.py         # Prompt VulnHunter, callback worker
```

---

## Features

| Feature | Description |
|---|---|
| **VulnHunter pipeline** | 4 phases : Recon → Hunt → Verify → Report |
| **Vérification adversariale** | Tentative systématique de réfutation |
| **Validation Docker réelle** | curl / ASAN / exec — pas d'auto-validation |
| **Format VULN-NNN** | Un finding par sink, avec CWE |
| **ZIP complet** | README + PoCs + exploit tests |
| **Popup modale** | Visualisation avec toggle raw/rendu MD |
| **Tous modèles** | Compatible Opus, DeepSeek, Gemini, etc. |

---

## License

MIT
