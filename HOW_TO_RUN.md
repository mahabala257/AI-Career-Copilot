# AI Career Copilot — Setup & Run Guide (Local Windows, No Docker)

This guide runs the entire stack natively on Windows: PostgreSQL installed directly,
Python virtual environment for the backend, ChromaDB as a local embedded vector
store (just a folder on disk — no separate server), and Node.js for the frontend.

---

## 1. Prerequisites — Install These First

| Tool | Version | Download |
|---|---|---|
| Python | 3.13 (NOT 3.14 — PyMuPDF has no prebuilt wheel for it yet) | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org |
| PostgreSQL | 14+ (16 recommended) | https://www.postgresql.org/download/windows/ |
| Google Gemini API key | free | https://aistudio.google.com/app/apikey |

**Python install:** check **"Add Python to PATH"** during installation.

**PostgreSQL install:** the installer will ask you to set a password for the
`postgres` superuser — remember it, you'll need it below. Keep the default port
`5432`. The installer also installs **pgAdmin** (a GUI) and the `psql` command-line
tool — both are useful but optional.

> Note: earlier versions of this project pinned `chromadb==0.5.11`, which
> depends on `chroma-hnswlib==0.7.6` — a package with **no prebuilt wheel for
> Python 3.13 on Windows**. pip would fall back to compiling it from source,
> which fails with `fatal error C1083: Cannot open include file: 'float.h'`
> or `'io.h'` even with Visual Studio Build Tools and the Windows SDK
> installed. This has been fixed: `requirements.txt` now pins
> `chromadb==1.5.9`, which ships as a universal prebuilt wheel
> (`cp39-abi3-win_amd64`) with no C++ extension to compile at all. The
> `asyncpg` and `psycopg2-binary` versions are also pinned to releases with
> prebuilt Windows wheels for Python 3.13. As long as you use Python 3.13
> (not 3.14) and the versions in `requirements.txt` as provided, `pip install`
> should complete with no compiler required.

---

## 2. Clone / Extract the Project

Extract the project anywhere on your PC, e.g. `D:\LT` or `Desktop\LT`. This guide
assumes the project root contains a `backend/` folder and a `frontend/` folder
directly inside it (no extra `ai-career-copilot` subfolder).

---

## 3. Set Up PostgreSQL Database

Open **PowerShell** and create the database. Easiest way — using `psql`
(installed alongside PostgreSQL; you may need to add it to PATH or use the full
path, e.g. `"C:\Program Files\PostgreSQL\16\bin\psql.exe"`):

```powershell
psql -U postgres -c "CREATE DATABASE career_copilot;"
```

It will prompt for the `postgres` user password you set during install.

Alternative — using **pgAdmin** (GUI):
1. Open pgAdmin → connect to your local server
2. Right-click **Databases** → **Create** → **Database**
3. Name it `career_copilot` → Save

---

## 4. Backend Setup

Open PowerShell in the project root:

```powershell
cd backend

# Create virtual environment with Python 3.13 specifically
py -3.13 -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

If `pip install` fails partway through and you re-run it, that's normal — pip
will skip packages already installed and continue with the rest.

### Create the `.env` file

Inside `backend/`, create a file named `.env` (no file extension — if Notepad
adds `.txt`, rename it back to `.env`). Use this template:

```env
# ── Database ──────────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PG_PASSWORD@localhost:5432/career_copilot

# ── JWT ───────────────────────────────────────────────────────────────────
JWT_SECRET_KEY=replace-with-a-random-32+-character-string

# ── LLM (required) ───────────────────────────────────────────────────────
GOOGLE_API_KEY=your-gemini-api-key-here

# ── LLM (optional — speeds up quiz/interview generation) ────────────────
GROQ_API_KEY=

# ── Embeddings fallback (optional) ───────────────────────────────────────
# Only needed if Gemini's embedding API rejects your GOOGLE_API_KEY (a known
# issue with Google's newer "AQ."-prefix keys, which langchain-google-genai
# doesn't yet support). If set, ChromaDB seeding automatically falls back to
# OpenAI's embedding model whenever Gemini calls fail. Get a key at
# https://platform.openai.com/api-keys
OPENAI_API_KEY=

# ── Monitoring (optional) ────────────────────────────────────────────────
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=

# ── App ───────────────────────────────────────────────────────────────────
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
CHROMADB_PATH=./chroma_store
UPLOAD_DIR=./uploads
```

Replace:
- `YOUR_PG_PASSWORD` with the PostgreSQL password you set during install
- `JWT_SECRET_KEY` with a random string of at least 32 characters (generate one below)
- `GOOGLE_API_KEY` with your real Gemini key

**Generate a JWT secret in PowerShell (no Python dependency needed):**
```powershell
-join ((1..32) | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })
```
Copy the output into `JWT_SECRET_KEY`.

### Run database migrations

```powershell
alembic upgrade head
```

This creates all the tables (`users`, `resumes`, `skill_assessments`, LangGraph
checkpoint tables, etc.) inside `career_copilot`.

### Set up ChromaDB

ChromaDB here runs in **embedded/local mode** — it is not a server you start
separately. It's a Python library that persists vector data to a folder
(`./chroma_store`, as set by `CHROMADB_PATH`) the first time the backend runs.

Seed it with the initial knowledge base:

```powershell
python scripts/seed_chromadb.py
```

You should see a per-collection upsert summary. To check status later without
re-seeding:

```powershell
python scripts/seed_chromadb.py --status
```

(The backend's startup also auto-seeds empty collections, so this step is a
safety net more than a strict requirement — but run it once up front so you
can confirm everything is wired up correctly.)

### Start the backend

```powershell
uvicorn app.main:app --reload --port 8000
```

Backend running at: **http://localhost:8000**
Interactive API docs (Swagger UI): **http://localhost:8000/docs**

Leave this terminal running.

---

## 5. Frontend Setup

Open a **second** PowerShell window in the project root:

```powershell
cd frontend

npm install
```

### Create the frontend `.env`

Create a file named `.env` inside `frontend/`:

```env
VITE_API_URL=http://localhost:8000
```

### Start the frontend

```powershell
npm run dev
```

Frontend running at: **http://localhost:5173**

Open that URL in your browser. The frontend talks directly to the backend at
`localhost:8000` via the `VITE_API_URL` above (and Vite's dev proxy already
forwards `/api` and `/ws` to `localhost:8000`, configured in `vite.config.ts`).

---

## 6. Getting API Keys

### Google Gemini (required)
1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Paste into `backend/.env` as `GOOGLE_API_KEY`

### Groq (optional — faster quiz/interview generation)
1. Go to https://console.groq.com/keys
2. Create a new API key
3. Paste into `backend/.env` as `GROQ_API_KEY`

### LangFuse (optional — LLM call monitoring/tracing)
1. Go to https://cloud.langfuse.com and create a project
2. Copy the Public Key and Secret Key into `backend/.env`

---

## 7. Running Tests

```powershell
cd backend
venv\Scripts\activate

# Unit-style scripts (no running server needed)
python scripts/test_graph.py
python scripts/test_rag.py
python scripts/test_resume_agent.py

# Integration tests (requires the backend running + real API keys)
python tests/test_integration.py
```

---

## 8. Day-to-Day Usage (after first-time setup)

Every time you want to run the project:

**Terminal 1 — backend:**
```powershell
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend:**
```powershell
cd frontend
npm run dev
```

PostgreSQL runs as a Windows service in the background automatically once
installed — you don't need to start it manually. ChromaDB needs no separate
start step either; it just reads/writes the `chroma_store` folder.

---

## 9. Environment Variables Reference

**`backend/.env`:**

```env
# Required
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/career_copilot
GOOGLE_API_KEY=your-gemini-api-key
JWT_SECRET_KEY=32-character-random-string

# Optional
GROQ_API_KEY=
OPENAI_API_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=

# App settings
CHROMADB_PATH=./chroma_store
UPLOAD_DIR=./uploads
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
ENVIRONMENT=development
DEBUG=true
```

**`frontend/.env`:**

```env
VITE_API_URL=http://localhost:8000
```

---

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| `JWT_SECRET_KEY is set to an insecure placeholder` or `must be at least 32 characters` | Generate a real 32+ character random string (see Step 4) and put it in `backend/.env` |
| `connection refused` / `password authentication failed` on startup | Check `DATABASE_URL` in `backend/.env` matches your real Postgres password and that PostgreSQL service is running (Services app → "postgresql-x64-16" should say Running) |
| `pip install` tries to compile `chroma-hnswlib`/`asyncpg`/`psycopg2-binary` from source and fails with a missing `.h` file error (`float.h`, `io.h`) | This was a known issue with `chromadb==0.5.11` on Python 3.13 — fixed by pinning `chromadb==1.5.9` in `requirements.txt`, which ships a prebuilt wheel with no compilation needed. If you still hit this, confirm you're on Python 3.13 (not 3.14) and that `requirements.txt` has not been reverted to an older chromadb pin |
| `python` / `py` not found | Reinstall Python and check "Add Python to PATH", then open a fresh PowerShell window |
| `alembic upgrade head` fails with "database does not exist" | Re-run the `CREATE DATABASE career_copilot;` step in Section 3 |
| Frontend shows network errors / can't reach API | Confirm the backend terminal shows `Application startup complete` and is listening on port 8000; confirm `frontend/.env` has `VITE_API_URL=http://localhost:8000` |
| Port 8000 or 5173 already in use | Stop whatever is using it, or run uvicorn with `--port 8001` and update `VITE_API_URL` to match |
| ChromaDB seeding shows 0 documents seeded on every run | That's expected if it was already seeded earlier — use `python scripts/seed_chromadb.py --force` to re-seed |

---

## 11. Folder Structure

```
LT/
├── backend/                  # FastAPI + LangGraph
│   ├── app/
│   │   ├── agents/           # LangGraph agents
│   │   ├── api/routes/       # REST endpoints
│   │   ├── models/           # SQLAlchemy ORM
│   │   ├── rag/              # ChromaDB RAG layer
│   │   ├── scoring/          # Career readiness engine
│   │   ├── services/         # Business logic
│   │   ├── config.py
│   │   └── main.py
│   ├── scripts/              # Seeding + test scripts
│   ├── tests/                # Integration tests
│   ├── venv/                 # Python virtual environment (created locally)
│   ├── chroma_store/         # ChromaDB persistent data (created on first run)
│   ├── .env                  # Your local secrets (create this — not committed)
│   └── requirements.txt
├── frontend/                 # React + TypeScript
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/         # API client (axios)
│   │   ├── stores/           # Zustand auth store
│   │   └── types/
│   ├── .env                  # Your local frontend config (create this)
│   └── package.json
└── HOW_TO_RUN.md
```