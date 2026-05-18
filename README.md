# SAST IA — Analyse de Sécurité Automatisée (Open Source)

> Analyse statique de code, validation Docker, et rapports détaillés propulsés par l'IA.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Navigateur (User)                      │
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
│  port 9000 — machine locale                               │
│                                                           │
│  1. Code Fetcher — git clone / download upload            │
│  2. OpenCode Runner — lance @SastIA_manager               │
│     │                                                     │
│     ├─ @SastIA_docker   → environnement de test           │
│     ├─ @SastIA_analyzer → audit de sécurité               │
│     ├─ @SastIA_rapport  → rapport final Markdown          │
│     └─ POST callback    → /api/audits/{id}/callback       │
└──────────────────────────────────────────────────────────┘
```

### Structure du projet

```
sastIA/
├── backend/                    # API REST
│   ├── app/
│   │   ├── main.py             # Point d'entrée FastAPI
│   │   ├── config.py           # Configuration (settings, env)
│   │   ├── database.py         # SQLAlchemy engine + session
│   │   ├── models.py           # User, Audit
│   │   ├── schemas.py          # Pydantic validation
│   │   ├── auth.py             # JWT + bcrypt
│   │   ├── routers/
│   │   │   ├── auth.py         # Register, Login, Me
│   │   │   ├── audits.py       # CRUD, upload, callback, dispatch
│   │   │   └── reports.py      # Rapport + PDF
│   │   └── services/
│   │       ├── analysis.py     # Payload worker (legacy)
│   │       └── report.py       # Génération PDF (WeasyPrint)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # Application React
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.tsx        # Connexion
│   │   │   ├── Register.tsx     # Création de compte
│   │   │   ├── Dashboard.tsx    # Stats + vulnérabilités
│   │   │   ├── NewAudit.tsx     # Upload / Git + wizard
│   │   │   ├── AuditsList.tsx   # Liste filtrée
│   │   │   ├── AuditDetail.tsx  # Suivi temps réel
│   │   │   └── Report.tsx       # Visualisation + PDF
│   │   ├── components/          # Layout, UI, ProtectedRoute
│   │   ├── context/            # AuthContext (JWT)
│   │   └── api/                # Axios client
│   ├── package.json
│   └── Dockerfile
│
├── worker/                     # Worker d'analyse
│   ├── main.py                 # POST /analyze
│   ├── code_fetcher.py         # Récupération du code (git / upload)
│   ├── opencode_runner.py      # Lance @SastIA_manager
│   ├── Dockerfile
│   └── requirements.txt
│
├── .opencode/agents/           # Agents opencode SastIA
│   ├── sastia_manager.md       # Orchestrateur
│   ├── sastia_docker.md        # Environnement de test Docker
│   ├── sastia_analyzer.md      # Audit de sécurité
│   └── sastia_rapport.md       # Rédaction du rapport final
│
├── docker-compose.yml
└── README.md
```

---

## Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| **Inscription / Connexion** | JWT + bcrypt, protection des routes |
| **Dashboard** | Statistiques globales, compteurs par sévérité |
| **Nouvel audit** | Upload de code (ZIP, archives) ou URL de dépôt Git |
| **Analyse code** | Agents opencode d'analyse SAST (OWASP Top 10, CVSS) |
| **Validation Docker** | Build + test d'exploitation de l'image |
| **Rapports Markdown** | Rapport complet avec tableau des vulnérabilités |
| **Export PDF** | Téléchargement PDF formaté (WeasyPrint) |
| **Callback worker** | Pipeline asynchrone backend → worker → callback |
| **Polling temps réel** | Le frontend interroge le statut toutes les 10s |

---

## Flux utilisateur

```
1. Connexion / inscription → dashboard
2. "Nouvel audit" → wizard en 2 étapes
   ├── Étape 1 : Nom + description
   └── Étape 2 : Upload code ZIP / URL Git
3. Statut : pending → analyzing_code → (analyzing_docker) → completed
4. Dashboard → voir les vulnérabilités par sévérité
5. Rapport Markdown → visualisé dans l'interface
6. Export PDF → téléchargement
```

---

## API Complète

### Authentification

| Méthode | Endpoint | Corps | Réponse |
|---|---|---|---|
| `POST` | `/api/auth/register` | `{email, password, full_name, company?}` | `{access_token, user}` |
| `POST` | `/api/auth/login` | `{email, password}` | `{access_token, user}` |
| `GET` | `/api/auth/me` | — | `{id, email, full_name, ...}` |

### Audits

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/api/audits/dashboard` | Statistiques globales + 10 derniers audits |
| `GET` | `/api/audits/` | Liste de tous les audits |
| `POST` | `/api/audits/` | Créer un audit (multipart: name, description, repo_url, code_file, docker_analysis_enabled) |
| `GET` | `/api/audits/{id}` | Détail d'un audit |
| `POST` | `/api/audits/{id}/start` | Lancer l'analyse (envoie le job au worker) |
| `GET` | `/api/audits/{id}/download` | Télécharger le fichier code uploadé |
| `DELETE` | `/api/audits/{id}` | Supprimer un audit |

### Callback (worker → backend)

| Méthode | Endpoint | Corps |
|---|---|---|
| `POST` | `/api/audits/{id}/callback` | `{report_markdown, vulnerabilities?, docker_success?, error?}` |

### Rapports

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/api/reports/{id}` | Rapport Markdown |
| `GET` | `/api/reports/{id}/pdf` | Télécharger le PDF |

### Worker

| Méthode | Endpoint | Corps |
|---|---|---|
| `POST` | `/analyze` | `{audit_id, user_id, callback_url, repo_url?, code_path?, analysis_type, docker_analysis}` |
| `GET` | `/health` | Health check |

---

## Modèles de données

### User
```
id              UUID (PK)
email           String (unique)
password_hash   String (bcrypt)
full_name       String
company         String?
is_active       Integer
created_at      DateTime
updated_at      DateTime
```

### Audit
```
id                  UUID (PK)
user_id             UUID (FK → users)
name                String
description         Text?
repo_url            String?
code_file_path      String?
status              Enum: pending | analyzing_code | analyzing_docker | completed | failed
docker_status       Enum: not_started | pending | success | failed
vulnerabilities_*   Integer (critical, high, medium, low, info)
report_markdown     Text?
error_message       Text?
analysis_type       String
docker_analysis_enabled Integer
created_at          DateTime
completed_at        DateTime?
```

---

## Interfaces Frontend

### Login / Register (`/login`, `/register`)
- Design épuré, fond gradient
- Validation frontend + backend
- Affichage des erreurs (email déjà pris, mot de passe invalide)
- Lien navigation entre login/register

### Dashboard (`/dashboard`)
- 4 cartes stats (total, en cours, terminés, échecs)
- 4 vignettes vulnérabilités (critique, élevée, moyenne, basse)
- Liste des 10 derniers audits avec statut et badges par sévérité
- Bouton "Nouvel audit"
- Rafraîchissement automatique

### Nouvel audit (`/audits/new`)
- Wizard 2 étapes avec indicateur de progression
  - Étape 1 : Nom + description
  - Étape 2 : Glisser-déposer upload ou URL Git

### Liste des audits (`/audits`)
- Filtres par statut (Tous, En attente, Analyse code, Analyse Docker, Terminés, Échecs)
- Badges de sévérité par audit
- Vue détaillée au clic

### Détail audit (`/audits/:id`)
- Statut en temps réel (polling 10s)
- Icône animée pour "Analyse en cours"
- Résumé des vulnérabilités si terminé
- Boutons "Voir le rapport" et "Télécharger PDF"

### Rapport (`/audits/:id/report`)
- Rendu Markdown complet avec tableaux
- Support des emojis, code blocks, listes
- Bouton "Télécharger PDF" en haut et en bas

---

## Workflow Worker

```
POST /api/audits/{id}/start          ← déclenché par l'utilisateur
         │
         ▼
Backend POST → http://localhost:9000/analyze
         │
         ▼
Worker récupère le code
         │
         ├── repo_url ? git clone --depth 1
         └── code upload ? GET /api/audits/{id}/download + extraction
         │
         ▼
Worker lance opencode run SastIA_manager
         │
         ├─ @SastIA_docker
         │   ├─ Décompresse / clone le code
         │   ├─ Identifie l'environnement nécessaire
         │   ├─ Build une image Docker sécurisée (sans montage de volumes)
         │   └─ Lance l'application et vérifie qu'elle répond
         │   └─ Résultat : environnement prêt ou échec
         │
         ├─ @SastIA_analyzer
         │   ├─ Analyse globale de l'architecture et des entry points
         │   ├─ Audit fichier par fichier (OWASP Top 10, RCE, injections...)
         │   ├─ Test chaque vulnérabilité sur l'environnement Docker
         │   └─ Marque Validé / Non validé pour chaque finding
         │
         ├─ @SastIA_rapport
         │   ├─ Agrège les résultats de l'analyse
         │   ├─ Produit le rapport final formaté (tableau CVSS + détails)
         │   └─ POST callback → /api/audits/{id}/callback
         │       ├─ report_markdown
         │       └─ tableau des vulnérabilités parsé automatiquement
         │
         ▼
Backend reçoit le callback
         │
         ├─ report_markdown stocké dans la BDD
         ├─ compteurs (critical/high/medium/low) parsés du tableau
         ├─ statut → "completed"
         └─ l'utilisateur voit le résultat dans le dashboard
```

---

## Démarrage

### Prérequis
- Python 3.12+
- Node.js 20+
- Docker (optionnel)

### 1. Backend

```bash
cd backend
python3 -m venv ../venv
../venv/bin/pip install -r requirements.txt
../venv/bin/uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173 (ou 3001 si 3000 est pris)
```

### 3. Worker (nécessite opencode)

```bash
cd worker
python3 -m venv ../worker-venv
../worker-venv/bin/pip install -r requirements.txt
../worker-venv/bin/uvicorn main:app --reload --port 9000
```

> Le worker utilise `opencode run SastIA_manager` pour lancer l'analyse.
> Vérifie que les agents sont bien listés : `opencode agent list | grep SastIA`

### 4. Modèle IA

Par défaut, le worker utilise `opencode-go/deepseek-v4-flash`. Pour changer le modèle :

```bash
# Via variable d'environnement :
OPENCODE_MODEL=ollama-cloud/deepseek-v4-pro ../worker-venv/bin/uvicorn main:app --port 9000

# Modèles disponibles :
opencode-go/deepseek-v4-flash       ← rapide, défaut
opencode-go/deepseek-v4-pro         ← plus cher, plus complet
opencode/deepseek-v4-flash-free     ← gratuit, limité
ollama-cloud/deepseek-v4-flash      ← via Ollama Cloud
ollama-cloud/deepseek-v4-pro        ← via Ollama Cloud
```

### 4. Avec Docker (tout en un)

```bash
docker-compose up -d --build
# Backend : http://localhost:8000
# Frontend : http://localhost:3000
# Worker : http://localhost:9000 (profil "full")
```

### 5. Configuration

Créez un fichier `.env` dans `backend/` :

```env
DATABASE_URL=sqlite:///./sastia.db
SECRET_KEY=votre-cle-secrete-tres-longue
WORKER_URL=http://localhost:9000
CODE_DOWNLOAD_BASE_URL=http://localhost:8000
```

### 6. Variables Worker

| Variable | Défaut | Description |
|---|---|---|
| `WORK_DIR` | `/tmp/sastia-worker` | Répertoire de travail du worker (code cloné, logs) |
| `OPENCODE_MODEL` | `opencode-go/deepseek-v4-flash` | Modèle IA utilisé par opencode |

### 7. Logs et débogage

Le worker écrit les logs de l'agent opencode en temps réel :

**Fichier de log (sur le disque) :**
```bash
tail -f /tmp/sastia-worker/{audit_id}/opencode.log
```

**HTTP (via le worker) :**
```bash
curl http://localhost:9000/log/{audit_id}
```

Structure des fichiers dans `/tmp/sastia-worker/{audit_id}/` :
```
code/                  ← code source cloné / extrait
opencode.log          ← log temps réel de l'agent (stdout + stderr)
agent-partial.md      ← dernier résultat partiel sauvegardé (même en cas de timeout)
```

---

## Agents OpenCode (`.opencode/agents/`)

4 agents subagent opencode orchestrés par `@SastIA_manager` :

### @SastIA_manager — Orchestrateur

Point d'entrée unique. Reçoit le chemin du code et l'URL de callback. Délègue chaque étape aux agents spécialisés.

### @SastIA_docker — Environnement de test

- Décompresse le code ou clone le dépôt GitHub
- Analyse le code pour déterminer l'environnement nécessaire
- Construit une image Docker sécurisée (pas de montage de volumes host)
- Lance l'application et vérifie qu'elle est accessible
- Contrainte : l'image ne doit jamais compromettre le host

### @SastIA_analyzer — Audit de sécurité

- Analyse globale de l'architecture (entry points, surface d'attaque)
- Audit fichier par fichier :
  - Web : OWASP Top 10 (XSS, SQLi, CSRF, IDOR...)
  - Autre : RCE, buffer overflow, heap spray, attaques BDD...
- Test chaque vulnérabilité sur l'environnement Docker
- Marque chaque finding : **Validé** (exploitable) / **Non validé** (faux positif probable)

### @SastIA_rapport — Rapport final

- Agrège les résultats de @SastIA_analyzer
- Produit un rapport structuré avec :
  - Tableau récapitulatif Critical / High / Medium / Low
  - Détail par finding : fichier:ligne, CVSS, description, impact, reproduction, correction
- Envoie le rapport final à l'URL de callback du backend

### Format du tableau (obligatoire pour le parsing auto)

```markdown
| Severity | Count |
|----------|-------|
| Critical | N     |
| High     | N     |
| Medium   | N     |
| Low      | N     |
```

C'est ce tableau qui est parsé automatiquement par le backend pour remplir les compteurs de vulnérabilités dans la BDD et le dashboard.

---

## Déploiement Worker distant

Le worker peut tourner sur une machine séparée (ex : serveur dédié avec GPU, opencode, Docker).

Modifie `backend/.env` pour pointer vers le worker distant :

```env
WORKER_URL=http://<ip-worker>:9000
CODE_DOWNLOAD_BASE_URL=http://<ip-backend>:8000
```

Le backend enverra le job au worker qui :
1. Clone le dépôt Git ou télécharge le code via l'API backend
2. Lance `opencode run SastIA_manager` avec le chemin du code et l'URL de callback
3. `@SastIA_manager` orchestre `@SastIA_docker` → `@SastIA_analyzer` → `@SastIA_rapport`
4. `@SastIA_rapport` POST le rapport final vers le backend

> Note : le worker DOIT avoir opencode installé et les agents SastIA disponibles dans `.opencode/agents/`.

---

## Licence

MIT