# AI Career Copilot — Project Report

**Project Title:** AI Career Copilot — Agentic AI-Powered Career Development Platform
**Developer:** Mahalakshmi Bala
**Institution:** Rajalakshmi Engineering College, Chennai
**Department:** Artificial Intelligence and Data Science
**Internship Organisation:** Larsen & Toubro Construction, Porur, Chennai
**Seminar Title:** From Artificial Intelligence to Agentic AI

---

## 1. Abstract

AI Career Copilot is a production-grade multi-agent AI platform that helps students,
fresh graduates, and job seekers accelerate their career preparation. Built on a
LangGraph-orchestrated multi-agent architecture, the platform provides:
resume ATS analysis, skill gap identification, interview question generation,
MCQ quiz assessment, and personalised study planning — all powered by Google Gemini
and grounded in real job-market knowledge via ChromaDB RAG (Retrieval-Augmented Generation).

The system demonstrates the transition from traditional AI (single-purpose models)
to Agentic AI (autonomous, multi-step, tool-using agents) as described in the
accompanying engineering seminar.

---

## 2. Problem Statement

Engineering students in India face three critical challenges when entering the job market:

1. **Resume Blindness** — Students submit resumes without knowing their ATS compatibility
   score or what skills recruiters are looking for. 70% of resumes are rejected by ATS
   before a human reads them.

2. **Skill Gap Ignorance** — Students do not know the precise gap between what they know
   and what the market requires for their target role, leading to unfocused preparation.

3. **Unstructured Preparation** — Without a personalised roadmap, students prepare
   randomly, wasting time on low-impact topics while missing critical skills.

**AI Career Copilot solves all three** with a single platform that analyses, advises,
and plans — powered by the same LLM technology used by leading tech companies.

---

## 3. System Architecture

### 3.1 Overall Architecture

```
User (Browser)
      │
React Frontend (Vite + TypeScript + Tailwind + shadcn/ui)
      │ JWT + REST API
FastAPI Backend (Python 3.12)
      │
LangGraph Orchestration Layer
      │
Supervisor Agent (Gemini 2.0 Flash)
      │ Conditional Routing
      ├── Resume Agent         (Gemini 2.0 Flash + ChromaDB RAG)
      ├── Skill Gap Agent      (Gemini 2.0 Flash + ChromaDB RAG)
      ├── Interview Agent      (Gemini 2.0 Flash)
      ├── Quiz Agent           (Gemini 2.0 Flash)
      └── Study Planner Agent  (Gemini 2.0 Flash)
                │
        ┌───────┴────────┐
   ChromaDB           PostgreSQL
  (RAG Store)       (User Data)
```

### 3.2 LangGraph Multi-Agent Flow

```
User Message
    ↓
Supervisor Agent → Analyses intent → Decides routing
    ↓
Agent Router → Dispatches to specialist agent(s)
    ↓
Specialist Agent → Queries ChromaDB for context → Calls Gemini → Returns structured output
    ↓
Response Synthesizer → Combines all outputs → Extracts recommendations
    ↓
FastAPI → Returns JSON → React renders UI
```

### 3.3 RAG Pipeline

```
Seed Documents (seed_documents.py)
    ↓
Gemini text-embedding-004 (768-dim vectors)
    ↓
ChromaDB PersistentClient (cosine similarity, HNSW index)
    ↓
Per-agent semantic retrieval (retrieve_for_agent)
    ↓
Retrieved chunks injected into Gemini prompt
    ↓
Grounded, factual response
```

---

## 4. Technology Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Frontend | React 18 + TypeScript | Industry standard, type safety |
| Styling | Tailwind CSS + shadcn/ui | Rapid professional UI |
| State | Zustand | Lightweight, simple auth state |
| API Client | Axios + React Query | Auto-retry, caching, loading states |
| Backend | FastAPI | Async Python, auto-docs, fast |
| Auth | JWT (python-jose) + bcrypt | Industry standard, stateless |
| ORM | SQLAlchemy 2.0 async | Type-safe, async DB access |
| Migrations | Alembic | Version-controlled schema changes |
| Database | PostgreSQL | Relational, JSONB for flexible data |
| AI Framework | LangGraph | Stateful multi-agent orchestration |
| LLM | Google Gemini 2.0 Flash | Fast, free tier, 1M tokens/day |
| Embeddings | Gemini text-embedding-004 | 768-dim, semantic similarity |
| Vector DB | ChromaDB | Local, free, no API costs |
| PDF Parsing | PyMuPDF (fitz) | Fast, accurate text extraction |
| Deployment | Vercel (frontend) + Render (backend) | Free tier, auto-deploy |

**Local development:** the project runs entirely without Docker — a Python
virtual environment for the backend, a locally installed PostgreSQL server, and
ChromaDB in embedded mode (a persisted folder on disk, no separate service to
run). See `HOW_TO_RUN.md` for the full native Windows setup and `SETUP.md` for
the condensed quick-start version.

---

## 5. Features Implemented

### Phase 1 (Core — Fully Built)

#### 5.1 Authentication System
- User registration with email + password (bcrypt hashed)
- JWT access tokens (30 min) + refresh tokens (7 days)
- Auto-refresh on token expiry (transparent to user)
- Protected routes — all endpoints require valid JWT
- User profile with target role and skills

#### 5.2 Resume Agent
- PDF upload via drag-and-drop (up to 10 MB)
- PyMuPDF text extraction with 7-step cleaning pipeline
  (ligatures, hyphenated breaks, decorative lines, page numbers)
- Gemini ATS analysis with:
  - ATS Score (0–100)
  - Extracted skills list
  - Missing skills for target role
  - 5-component score breakdown (skills match, experience, education, keywords, formatting)
  - Specific improvement suggestions
  - Experience level detection
- Resume history with previous analyses
- Results persisted to PostgreSQL

#### 5.3 Skill Gap Agent
- Compares user's skills against job market requirements for target role
- Reads extracted skills from Resume Agent output (no duplicate LLM call)
- RAG-grounded: ChromaDB job requirements collection queried first
- Output:
  - Overall readiness percentage (0–100%)
  - Missing skills with priority (critical/high/medium/low)
  - Time-to-learn estimates per skill
  - Learning resource recommendations
  - Priority learning order
  - Months to job-ready estimate
  - Immediate action items
- Persists updated skills to user profile

#### 5.4 Interview Agent
- Three interview types: HR, Technical, Coding
- Three difficulty levels: Easy, Medium, Hard
- Role-specific questions (different for AI Engineer vs Data Scientist)
- Technical questions grounded in ChromaDB interview Q&A collection
- Answer evaluation via second Gemini call:
  - Per-question scores (0–10)
  - Strengths and improvements
  - Overall readiness score
  - Interview tips
- Session history persisted to PostgreSQL

#### 5.5 Quiz Agent
- MCQ and coding quiz types
- Auto topic selection from skill gap priority order
- 10-question MCQ with 4 options each
- Two-step scoring:
  - Instant exact-match scoring (no LLM, zero latency)
  - Gemini weak area analysis and topic clustering
- Detailed results: per-question correctness, weak areas, strong areas
- Improvement recommendations
- Quiz history in PostgreSQL

#### 5.6 Study Planner Agent
- Three plan types: Daily, Weekly, Monthly
- Uses outputs from ALL previous agents:
  - Skill gaps → what to learn
  - Quiz weak areas → what to reinforce
  - Resume analysis → current level
- Daily: session-by-session breakdown with specific tasks and resources
- Weekly: 7-day theme with career actions and week project
- Monthly: 4-week milestones with deliverables
- Plans persisted and retrievable

#### 5.7 ChromaDB RAG Layer
- 5 collections: interview_questions, job_requirements, learning_resources, career_guidance, company_info
- 28 seed documents covering:
  - Technical interview Q&A (AI Engineer, Data Scientist, Backend Engineer)
  - Job market requirements for 5 roles
  - Learning resource recommendations (Python, ML, LangChain, Docker, FastAPI, DSA)
  - Career guidance (resume writing, LinkedIn, job search, portfolio)
  - Company information (TCS, Zoho, Google, Freshworks)
- Gemini text-embedding-004 (768-dim cosine similarity)
- Hash-based fallback for development without API key
- Auto-seeds on server startup if collections are empty
- Minimum 40% similarity threshold — no irrelevant results

#### 5.8 Career Readiness Score Engine
- Weighted aggregation:
  - Resume Score × 0.30
  - Skill Score × 0.25
  - Quiz Score × 0.25
  - Interview Score × 0.20
- Grade system: Excellent / Good / Developing / Early Stage / Getting Started
- Score history for trend charts
- Top 3 priority recommendations
- Dashboard radial chart visualisation

#### 5.9 React Frontend (7 Pages)
- **Dashboard** — Career score gauge, score trend chart, quick action grid
- **Resume Analyzer** — PDF dropzone, analysis results, skill badges, history
- **Skill Gap** — Role input, readiness progress, missing skills with priorities
- **Interview Center** — Type/difficulty selector, question cards, answer submission, evaluation
- **Quiz Center** — Topic selector, MCQ interface, instant scoring, results
- **Study Planner** — Plan type selector, daily/weekly/monthly views
- **Profile** — Name/role/skills management, score summary

---

## 6. API Endpoints (18 total)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Create account |
| POST | /api/auth/login | Get JWT tokens |
| POST | /api/auth/refresh | Refresh access token |
| GET | /api/auth/me | Current user profile |
| PATCH | /api/auth/me | Update profile |
| POST | /api/auth/logout | Invalidate session |
| POST | /api/resume/analyze | Upload + analyse resume |
| GET | /api/resume/history | Past resume analyses |
| GET | /api/resume/{id} | Specific analysis |
| POST | /api/skills/analyze | Run skill gap analysis |
| GET | /api/skills/profile | User skills profile |
| POST | /api/interview/generate | Generate questions |
| POST | /api/interview/evaluate | Evaluate answers |
| GET | /api/interview/history | Past sessions |
| POST | /api/quiz/generate | Generate quiz |
| POST | /api/quiz/submit | Submit + score answers |
| POST | /api/planner/generate | Generate study plan |
| GET | /api/planner/current | Active plans |
| GET | /api/progress/score | Career readiness score |
| GET | /api/progress/history | Score trend data |
| GET | /health | System health check |

---

## 7. Database Schema

### Tables
| Table | Purpose | Key Fields |
|-------|---------|-----------|
| users | Account data | id, email, hashed_password, target_role, current_skills |
| user_sessions | Login sessions + LangGraph thread IDs | id, user_id, refresh_token_hash |
| resumes | Resume files + analysis results | id, user_id, ats_score, extracted_skills, missing_skills |
| quiz_results | Quiz attempts + scores | id, user_id, topic, questions, score, weak_areas |
| interview_sessions | Mock interview records | id, user_id, session_type, questions, readiness_score |
| career_scores | Readiness score snapshots | id, user_id, overall_score, components, computed_at |
| study_plans | Generated study plans | id, user_id, plan_type, plan_data, is_active |

---

## 8. LangGraph Design

### State Schema (`CareerCopilotState`)
A single TypedDict shared across all agents with 25+ fields covering:
- User identity (user_id, session_id)
- Input context (user_message, target_role, resume_text)
- Agent control (next_agent, agent_queue, agents_called)
- Agent outputs (resume_analysis, skill_gap_analysis, interview_output, quiz_output, study_plan_output)
- RAG context (rag_context — injected before each agent)
- Error handling (error, error_agent)

### Key Design Decisions
1. **Shared state** — All agents read from and write to one state dict.
   Resume Agent's `extracted_skills` flows directly into Skill Gap Agent without
   an extra LLM call.

2. **Reducer pattern** — `agent_queue` and `agents_called` use `operator.add` reducer
   so list fields append instead of replacing — enabling multi-agent queue routing.

3. **Graceful degradation** — Every agent catches all exceptions and writes to
   `state["error"]` instead of raising. The graph never crashes for a user session.

4. **Keyword fallback routing** — Supervisor uses Gemini for routing but falls back
   to keyword matching if the API key is missing or the call fails.

5. **MemorySaver** — Per-user session memory via `thread_id = user_id`.
   Conversation context persists across requests within a server lifetime.

---

## 9. Challenges and Solutions

| Challenge | Solution |
|-----------|----------|
| Gemini rate limits (15 req/min free) | InMemoryRateLimiter at 14/min, shared across all agents |
| LLM returns non-JSON or markdown-fenced JSON | 4-strategy robust parser: strip fences → find outermost `{}` → fix trailing commas → parse |
| ChromaDB v1.5.9 requires `name()` method | Added `name()` to both GeminiEmbeddingFunction and HashEmbeddingFunction |
| JWT refresh race condition | Request queuing with `isRefreshing` flag in Axios interceptor |
| PDF text extraction artifacts | 7-step cleaning pipeline (ligatures, line-break hyphens, decorative lines, page numbers) |
| Multi-agent queue routing | `agents_called` list with `operator.add` reducer tracks which agents ran; router skips already-called agents |

---

## 10. Testing

### Unit Tests (scripts/)
| Script | Tests | Coverage |
|--------|-------|---------|
| test_graph.py | 8 tests | LangGraph routing, supervisor fallback, multi-agent queue |
| test_resume_agent.py | 9 tests | PDF parsing, JSON parsing, score enrichment, error states |
| test_rag.py | 7 tests | ChromaDB client, embeddings, seeding, retrieval, pipeline |

### Integration Tests (tests/test_integration.py)
15 end-to-end tests covering:
- Health check
- Auth (register, login, wrong password, no token)
- Resume upload and analysis
- Skill gap analysis
- Interview generation and evaluation
- Quiz generation and submission
- Study plan generation
- Career readiness score
- Input validation (wrong file type, empty fields, non-existent IDs)

---

## 11. Project Metrics

| Metric | Value |
|--------|-------|
| Total Python files | 48 |
| Total TypeScript/TSX files | 20 |
| Backend lines of code | ~4,200 |
| Frontend lines of code | ~1,800 |
| API endpoints | 21 |
| LangGraph agents | 5 (Phase 1) |
| ChromaDB collections | 5 |
| Seed documents | 28 |
| Database tables | 7 |
| Test scripts | 4 |
| Total tests | 39 |
| Steps completed | 11/12 |

---

## 12. What Makes This Project Special

1. **Real Agentic AI** — Not just LLM API calls wrapped in a web app.
   A true multi-agent system where agents collaborate, share state, and build
   on each other's outputs. Supervisor → Router → Agent → Synthesizer is the
   production pattern used at Anthropic, OpenAI, and Google.

2. **RAG grounding** — Responses are grounded in real job market data via ChromaDB,
   not just Gemini's training data. This is what separates reliable AI from hallucinating AI.

3. **Production patterns** — JWT auth, async SQLAlchemy, Alembic migrations,
   Pydantic validation, graceful error handling, rate limiting, retry logic,
   health endpoints — every production concern is addressed.

4. **Directly relevant to Indian engineering students** — The seed documents cover
   TCS, Zoho, Freshworks, Naukri, campus placement patterns, and the exact
   skills that 2024 Indian tech companies are hiring for.

5. **Seminar alignment** — Every concept from the "From AI to Agentic AI" seminar
   is demonstrated live: LLMs, RAG, embeddings, vector databases, LangChain,
   LangGraph, FastAPI, prompt engineering, multi-agent orchestration.

---

## 13. Future Enhancements (Phase 2 & 3)

### Phase 2 (Planned)
- Material Agent — YouTube, courses, documentation recommendations
- Company Research Agent — detailed company profiles and interview processes
- LinkedIn Optimisation Agent — headline, about, skills analysis
- Career Strategy Agent — long-term roadmap generation
- Groq integration for sub-second quiz and interview generation
- LangFuse monitoring dashboard

### Phase 3 (Planned)
- Spoken English Agent — grammar correction, professional rephrasing, HR simulation
- Wellness & Motivation Agent — study discipline, productivity advice
- Progress Tracking Agent — detailed analytics and badges
- MCP integrations: Google Calendar (schedule study plans), Google Drive (save reports)
- Voice input for spoken English practice
- Mobile app (React Native)

---

## 14. Conclusion

AI Career Copilot successfully demonstrates the full stack of modern Agentic AI
development — from LLM integration and multi-agent orchestration to RAG-grounded
retrieval, production-grade API design, and a complete React frontend.

The project bridges the gap between academic AI learning and real-world application,
providing a platform that is genuinely useful to the students it targets while
serving as a comprehensive technical showcase for modern AI engineering practices.

All five Phase 1 agents are fully implemented, all 21 API endpoints are functional,
all 7 frontend pages are production-ready, and the system runs natively on Windows
(Python virtual environment, locally installed PostgreSQL, and an embedded
ChromaDB store) for local development and demo purposes, with a documented path
to Render + Vercel for cloud deployment.

---

*Report prepared by Mahalakshmi Bala | AI & Data Science | Rajalakshmi Engineering College*
*Internship project at Larsen & Toubro Construction, Chennai*
