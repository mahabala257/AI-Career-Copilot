# AI Career Copilot — Setup Guide

A multi-agent, RAG-grounded career platform: **FastAPI + LangGraph** backend, **React + TypeScript** frontend, **PostgreSQL** database, and an embedded **ChromaDB** vector store. Runs natively on Windows — no Docker required.

---

## 1. Prerequisites

| Tool | Version | Download |
|---|---|---|
| Python | 3.13 (not 3.14) | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org |
| PostgreSQL | 14+ (16 recommended) | https://www.postgresql.org/download/windows/ |
| Groq API key | free | https://console.groq.com/keys |

> During Python install, tick **"Add Python to PATH."**
> During PostgreSQL install, remember the **postgres** password you set (needed below).

---

## 2. Create the Database

In PowerShell:

```powershell
psql -U postgres -c "CREATE DATABASE career_copilot;"
```

(Enter the postgres password when prompted. Alternatively, create a `career_copilot` database in pgAdmin.)

---

## 3. Backend Setup

```powershell
cd backend

# create + activate a Python 3.13 virtual environment
py -3.13 -m venv venv
venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

### Create `backend\.env`

Create a file named `.env` inside `backend\` with:

```env
# ── Database ─────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PG_PASSWORD@localhost:5432/career_copilot

# ── JWT (use a random 32+ character string) ──────────────
JWT_SECRET_KEY=replace-with-a-random-32-character-string

# ── LLM (required) ───────────────────────────────────────
GROQ_API_KEY=gsk_your_groq_key_here

# ── Optional ─────────────────────────────────────────────
GOOGLE_API_KEY=
OPENAI_API_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=

# ── App ──────────────────────────────────────────────────
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
CHROMADB_PATH=./chroma_store
UPLOAD_DIR=./uploads
```

Generate a JWT secret quickly in PowerShell:

```powershell
-join ((1..32) | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })
```

### Run migrations and seed the knowledge base

```powershell
alembic upgrade head
python scripts/seed_chromadb.py
```

(The backend also auto-seeds the vector store on first startup, so this is a safety net.)

### Start the backend

```powershell
python run.py
```

> **Use `python run.py`, not plain `uvicorn`.** `run.py` sets the Windows Selector event-loop policy, which the persistent LangGraph PostgreSQL checkpointer requires.

Backend: **http://localhost:8000** · API docs (Swagger): **http://localhost:8000/docs**

A healthy startup ends with:
```
[DB] OK
[Graph] Compiled with AsyncPostgresSaver (persistent memory ✓)
[RAG] Collections ready: 79 total documents
Server ready ✓
```

---

## 4. Frontend Setup

In a **second** terminal:

```powershell
cd frontend
npm install
```

Create `frontend\.env`:

```env
VITE_API_URL=http://localhost:8000
```

Start the frontend:

```powershell
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 5. First Use

1. Register a new account (name, email, password ≥ 8 characters, target role).
2. Upload a resume on the **Resume Analyzer** page to get an ATS score.
3. Explore the agents: Skill Gap, Interview, Quiz, Study Planner, and more.

---

## 6. Day-to-Day Run

PostgreSQL runs as a Windows service automatically; ChromaDB needs no separate start.

**Terminal 1 (backend):**
```powershell
cd backend
venv\Scripts\activate
python run.py
```

**Terminal 2 (frontend):**
```powershell
cd frontend
npm run dev
```

---

## 7. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Zustand, Axios |
| Backend | FastAPI (async Python), JWT auth, Pydantic |
| Agents | LangGraph (supervisor → specialist agents → synthesizer) |
| LLM | Llama 3.1 via Groq (provider-agnostic client) |
| RAG / Vector DB | ChromaDB with offline `all-MiniLM-L6-v2` embeddings |
| Database | PostgreSQL, async SQLAlchemy 2.0, Alembic |
| PDF parsing | PyMuPDF |

---

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `JWT_SECRET_KEY ... insecure` / `must be at least 32 characters` | Put a real 32+ char random string in `.env` |
| `connection refused` / `password authentication failed` | Check `DATABASE_URL` password and that the PostgreSQL service is running |
| AI features return empty / `429` | Groq free-tier rate limit — wait ~30–60 s and retry |
| Persistent memory falls back to MemorySaver | Launch with `python run.py` (not plain `uvicorn`) |
| `pip install` tries to compile a package | Confirm you are on Python 3.13 (not 3.14) |
| Port 8000 / 5173 already in use | Stop the other process, or change the port and update `VITE_API_URL` |
