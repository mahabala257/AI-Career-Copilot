# AI Career Copilot — Quick Setup Guide (No Docker)

This is the short version. For full detail and troubleshooting, see
[`HOW_TO_RUN.md`](./HOW_TO_RUN.md).

## Prerequisites
- Python 3.13
- Node.js 18+
- PostgreSQL 14+ installed and running locally
- A Google Gemini API key (free at https://aistudio.google.com/app/apikey)

## 1. Create the database

```powershell
psql -U postgres -c "CREATE DATABASE career_copilot;"
```

## 2. Backend

```powershell
cd backend
py -3.13 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PG_PASSWORD@localhost:5432/career_copilot
JWT_SECRET_KEY=your_random_32plus_char_secret_here
GOOGLE_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
CHROMADB_PATH=./chroma_store
UPLOAD_DIR=./uploads
```

Generate a secure JWT secret in PowerShell:
```powershell
-join ((1..32) | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })
```

Run migrations, seed ChromaDB, and start the server:

```powershell
alembic upgrade head
python scripts/seed_chromadb.py
uvicorn app.main:app --reload --port 8000
```

## 3. Frontend

Open a second terminal:

```powershell
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

Start it:

```powershell
npm run dev
```

## 4. Open the app

- **Frontend:** http://localhost:5173
- **Backend API docs:** http://localhost:8000/docs

## 5. Register and start using

1. Click "Register" and create an account
2. Set your target role (e.g. "AI Engineer")
3. Upload your resume PDF to get an ATS score
4. Use Skill Gap to see what skills you're missing
5. Go to Interview Center to practice
6. Take quizzes in Quiz Center
7. Generate a Study Plan

## Stopping

Press `Ctrl+C` in both terminal windows. PostgreSQL keeps running in the
background as a Windows service (it doesn't need to be "stopped" between
sessions — your data persists automatically).

## Troubleshooting

| Problem | Fix |
|---|---|
| `JWT_SECRET_KEY` error on startup | Make sure `.env` is present in `backend/` and the key is at least 32 characters |
| DB connection error | Check the PostgreSQL Windows service is running, and that `DATABASE_URL` has the correct password |
| Gemini API error | Check your `GOOGLE_API_KEY` in `backend/.env` |
| Port 8000 in use | Run `uvicorn app.main:app --reload --port 8001` and update `frontend/.env`'s `VITE_API_URL` to match |
| Port 5173 in use | Vite will automatically offer the next free port — check the terminal output |
| `pip install` compile errors on Windows (`chroma-hnswlib`, `float.h`/`io.h` missing) | Fixed in `requirements.txt` (`chromadb==1.5.9`, prebuilt wheel, no compiler needed). Make sure you're on Python 3.13, not 3.14 |

See [`HOW_TO_RUN.md`](./HOW_TO_RUN.md) for the complete walkthrough.
