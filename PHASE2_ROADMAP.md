# AI Career Copilot — Phase 2 Architecture Roadmap

**Document Type:** Architecture Design Plan  
**Based On:** Completed Phase 1 codebase (post production-readiness fixes)  
**Date:** June 2026  
**Status:** Planning — no code generated

---

## Phase 1 Recap (What Exists)

Before designing Phase 2, it's important to understand what Phase 1 already provides and where the integration points are.

**Existing agents:** Resume Agent, Skill Gap Agent, Interview Agent, Quiz Agent, Study Planner Agent  
**Existing graph:** `build_graph()` in `app/agents/graph.py` with `AgentName.PHASE_1_AGENTS` list  
**Existing state:** `CareerCopilotState` TypedDict in `app/agents/state.py`  
**Existing scoring engine:** `compute_career_readiness()` in `app/scoring/career_readiness.py` with 4 weighted components (resume 30%, skill 25%, quiz 25%, interview 20%)  
**Existing ChromaDB collections:** `interview_questions`, `learning_resources`, `company_info`, `career_guidance`, `job_requirements`  
**Existing DB tables:** `users`, `user_sessions`, `resumes`, `quiz_results`, `interview_sessions`, `career_scores`, `study_plans`  
**Existing `AgentName` stubs for Phase 2:** `COMPANY_RESEARCH`, `LINKEDIN`, `SPOKEN_ENGLISH`, `WELLNESS` already declared

Phase 2 plugs directly into this architecture — every agent follows the same node/state/route pattern already established.

---

## Phase 2 Overview

```
Phase 1 (Complete)          Phase 2 (This Plan)
──────────────────          ────────────────────
Supervisor Agent      ──→   Supervisor (extended routing)
Resume Agent          ──→   + Company Research Agent
Skill Gap Agent       ──→   + Internship Research Agent
Interview Agent       ──→   + Project Recommendation Agent
Quiz Agent            ──→   + LinkedIn Optimization Agent
Study Planner Agent   ──→   + Spoken English Agent
                            + Wellness & Motivation Agent
```

All 6 Phase 2 agents are **LangGraph nodes** that slot into the existing `StateGraph`. The Supervisor's routing table and prompt are updated once to include all new agents. No existing agents are modified.

---

## Agent 1 — Company Research Agent

### Responsibilities

Researches target companies and produces a structured preparation guide. Given a company name and target role, it retrieves company culture, interview style, tech stack, mission, known interview questions, and generates a tailored preparation strategy. Cross-references with the user's resume skills (from Resume Agent output in state) to highlight alignment and gaps.

### Inputs

| Input | Source | Description |
|---|---|---|
| `company_name` | API request / user message | "Google", "Microsoft", "Zoho", etc. |
| `target_role` | `state["target_role"]` | Role the user is interviewing for |
| `resume_analysis` | `state["resume_analysis"]` | Skill list from Phase 1 Resume Agent (if run) |
| `rag_context` | ChromaDB `company_info` collection | Retrieved company-specific documents |

### Outputs

State field: `company_research_output: dict`

```json
{
  "company_name": "Google",
  "overview": "Brief company mission and culture summary",
  "tech_stack": ["Go", "Python", "Kubernetes", "Spanner"],
  "interview_style": "4-5 rounds: phone screen, 2 technical, system design, hiring committee",
  "culture_values": ["Innovation", "Data-driven decisions", "Inclusion"],
  "known_questions": [
    { "type": "behavioral", "question": "Tell me about a time you had competing priorities." },
    { "type": "technical",  "question": "Design a URL shortener." }
  ],
  "skill_alignment": {
    "matching":  ["Python", "SQL"],
    "missing":   ["Go", "Kubernetes"],
    "alignment_score": 62
  },
  "prep_strategy": [
    "Focus on system design — Google values scalability thinking",
    "Practice LeetCode medium/hard for 3 weeks before interview",
    "Read the Google SWE book"
  ],
  "glassdoor_rating": 4.4,
  "typical_timeline": "4-6 weeks from application to offer"
}
```

### LangGraph Integration

**Node name:** `AgentName.COMPANY_RESEARCH` = `"company_research_agent"` (already declared in Phase 1 `AgentName`)

**graph.py changes:**
```
graph.add_node(AgentName.COMPANY_RESEARCH, company_research_agent_node)

# Add to post-agent routing map (same pattern as all Phase 1 agents)
# Add to Supervisor's conditional edge mapping
# Add to PHASE_2_AGENTS list
```

**Supervisor routing trigger phrases:** "research [company]", "prepare for [company] interview", "tell me about [company]", "what's [company] like", "Google interview prep"

**State reads:** `target_role`, `resume_analysis.extracted_skills`  
**State writes:** `company_research_output`

### ChromaDB Collections Required

**New collection: `company_profiles`**

| Field | Type | Description |
|---|---|---|
| `document` | string | Company profile chunk (culture, values, tech) |
| `metadata.company` | string | "google", "microsoft", "amazon" |
| `metadata.category` | string | "culture" \| "tech_stack" \| "interview_process" \| "questions" |
| `metadata.role_relevance` | string | "engineering" \| "data" \| "general" |
| `metadata.source` | string | "glassdoor" \| "internal" \| "leetcode" |

**Seed content needed:**
- Top 20 companies: Google, Microsoft, Amazon, Meta, Apple, Zoho, Infosys, TCS, Wipro, Accenture, Flipkart, Swiggy, Zepto, Razorpay, PhonePe, Freshworks, BYJU'S, Ola, Paytm, Meesho
- For each: tech stack, interview rounds, culture, known question types

**Existing `company_info` collection** (already in Phase 1 `CollectionName`) — rename or extend this. It exists but is empty in Phase 1 seeds. Phase 2 populates it.

### API Endpoints Required

```
POST /api/company/research
     Body: { "company_name": str, "target_role": str }
     Response: CompanyResearchResponse

GET  /api/company/search?q=google
     Response: list of matching company names (autocomplete)

GET  /api/company/history
     Response: list of past company researches for current user

GET  /api/company/{company_slug}
     Response: cached company profile (avoids re-running LLM for same company)
```

### Database Schema Changes

**New table: `company_researches`**

```sql
CREATE TABLE company_researches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name    VARCHAR(100) NOT NULL,
    target_role     VARCHAR(100),
    research_data   JSONB,           -- full CompanyResearchOutput
    alignment_score INTEGER,         -- 0-100, skill match %
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_company_researches_user_id ON company_researches(user_id);
CREATE INDEX ix_company_researches_company ON company_researches(company_name);
```

**`users` table: no changes needed**  
**`career_scores` table: add `company_score INTEGER` column** (contributes 10% to overall, redistributed from interview_score)

### Scoring Engine Impact

Phase 2 weight redistribution in `career_readiness.py`:

```
Phase 1 weights:          Phase 2 weights:
  resume_score    30%       resume_score      25%
  skill_score     25%       skill_score       20%
  quiz_score      25%       quiz_score        20%
  interview_score 20%       interview_score   20%
                            linkedin_score    10%  ← new
                            project_score      5%  ← new
```

### Estimated Implementation Effort

| Task | Effort |
|---|---|
| `company_research_agent.py` (LangGraph node) | 1.5 days |
| `company_research_prompts.py` (Gemini prompts) | 0.5 days |
| `company_research_service.py` (DB persistence) | 0.5 days |
| `schemas/company.py` (Pydantic schemas) | 0.5 days |
| `api/routes/company.py` (4 endpoints) | 1 day |
| ChromaDB seed data (20 companies) | 2 days |
| `graph.py` integration | 0.5 days |
| Supervisor prompt update | 0.5 days |
| Frontend: Company Research page | 2 days |
| **Total** | **~9 days** |

---

## Agent 2 — Internship Research Agent

### Responsibilities

Specialised variant of Company Research focused on internship seekers (students). Generates internship-specific preparation content: which companies hire interns for a given role, what the selection process looks like, what stipend/perks to expect, what projects interns typically work on, and what skills are needed to stand out. Also generates a tailored cover letter outline and application timeline.

Distinct from Company Research because internship processes differ fundamentally: aptitude tests, group discussions, shorter timelines, college-specific hiring, stipend ranges, and PPO (Pre-Placement Offer) likelihood.

### Inputs

| Input | Source | Description |
|---|---|---|
| `target_role` | `state["target_role"]` | "Software Engineer Intern", "Data Science Intern" |
| `education_level` | API request | "B.Tech 2nd year", "MBA 1st year" |
| `college_tier` | API request | "IIT/NIT", "Tier 2", "Tier 3" (affects which companies to target) |
| `available_from` | API request | Start date (e.g. "May 2025") |
| `resume_analysis` | `state["resume_analysis"]` | Current skills from Phase 1 |

### Outputs

State field: `internship_research_output: dict`

```json
{
  "recommended_companies": [
    {
      "company": "Microsoft",
      "program_name": "Microsoft Explore",
      "application_window": "August - October",
      "stipend_range": "₹80,000 - ₹1,00,000/month",
      "selection_process": ["Online coding test", "2 technical rounds", "HR round"],
      "ppo_likelihood": "High (60-70% of interns get PPO)",
      "required_skills": ["C++", "Data Structures", "Problem Solving"],
      "fit_score": 78
    }
  ],
  "application_timeline": {
    "3_months_before": "Build 2 strong projects, update GitHub",
    "2_months_before": "Apply to all targets, start DSA practice",
    "1_month_before":  "Mock interviews, system design basics",
    "1_week_before":   "Company-specific prep, read about products"
  },
  "cover_letter_outline": "...tailored outline...",
  "skill_gaps_for_internships": ["System Design basics", "Git workflow"],
  "top_platforms": ["LinkedIn", "Internshala", "Unstop", "company career pages"]
}
```

### LangGraph Integration

**Node name:** `AgentName.INTERNSHIP_RESEARCH` = `"internship_research_agent"` (add to `AgentName`)

**Relationship to Company Research:** These are sibling nodes, not parent-child. The Supervisor decides which to call based on user context (student vs experienced professional). A user can trigger both in sequence for comprehensive preparation.

**Supervisor routing trigger phrases:** "internship", "intern prep", "campus hiring", "summer internship", "college placement", "off-campus"

**State reads:** `target_role`, `resume_analysis`  
**State writes:** `internship_research_output`

### ChromaDB Collections Required

**New collection: `internship_programs`**

| Field | Type | Description |
|---|---|---|
| `document` | string | Internship program details |
| `metadata.company` | string | Company name |
| `metadata.program_type` | string | "summer" \| "winter" \| "year_round" |
| `metadata.education_level` | string | "undergraduate" \| "postgraduate" |
| `metadata.country` | string | "india" \| "us" \| "uk" |
| `metadata.stipend_tier` | string | "high" \| "medium" \| "low" |

**Seed content needed:**
- Top 30 internship programs in India (especially tech)
- FAANG intern programs
- Product-based company programs (Zoho, Freshworks, Razorpay)
- Government/PSU internship programs
- Startup internship landscape

### API Endpoints Required

```
POST /api/internship/research
     Body: { "target_role": str, "education_level": str, "college_tier": str, "available_from": str }
     Response: InternshipResearchResponse

GET  /api/internship/companies?role=software-engineer
     Response: list of companies with internship programs for that role

GET  /api/internship/timeline?start_date=2025-05-01
     Response: week-by-week application timeline

GET  /api/internship/history
     Response: past internship research sessions
```

### Database Schema Changes

**New table: `internship_researches`**

```sql
CREATE TABLE internship_researches (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_role             VARCHAR(100),
    education_level         VARCHAR(50),
    college_tier            VARCHAR(20),
    available_from          VARCHAR(20),
    research_data           JSONB,
    recommended_companies   JSONB,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_internship_researches_user_id ON internship_researches(user_id);
```

**`users` table: add `education_level VARCHAR(50)` and `college_name VARCHAR(100)` columns** — needed for internship targeting.

### Estimated Implementation Effort

| Task | Effort |
|---|---|
| `internship_research_agent.py` | 1.5 days |
| `internship_research_prompts.py` | 0.5 days |
| `internship_research_service.py` | 0.5 days |
| `schemas/internship.py` | 0.5 days |
| `api/routes/internship.py` (4 endpoints) | 1 day |
| ChromaDB seed data (30 programs) | 1.5 days |
| `graph.py` + Supervisor update | 0.5 days |
| Frontend: Internship Research page | 2 days |
| **Total** | **~8 days** |

---

## Agent 3 — Project Recommendation Agent

### Responsibilities

Recommends specific, buildable projects tailored to the user's target role, current skill level, and skill gaps. Not generic ("build a CRUD app") — specific and portfolio-optimised ("Build a real-time stock price alert system using FastAPI WebSockets, Redis pub/sub, and Telegram Bot API — this directly targets your SDE-2 role at fintech companies"). Each recommendation includes: what to build, why it matters for the role, which skills it demonstrates, estimated time to complete, tech stack, GitHub README structure, and how to present it in interviews.

Cross-references with Resume Agent output to avoid recommending projects the user already has, and with Skill Gap Agent to prioritise projects that close the highest-priority gaps.

### Inputs

| Input | Source | Description |
|---|---|---|
| `target_role` | `state["target_role"]` | e.g. "ML Engineer" |
| `skill_gap_analysis` | `state["skill_gap_analysis"]` | Missing skills from Phase 1 |
| `resume_analysis` | `state["resume_analysis"]` | Existing projects (extracted from resume text) |
| `experience_level` | API request | "fresher" \| "1-2 years" \| "3-5 years" |
| `time_available` | API request | Weeks available to build |

### Outputs

State field: `project_recommendations_output: dict`

```json
{
  "recommended_projects": [
    {
      "rank": 1,
      "title": "AI-Powered Resume Screener",
      "description": "Build a FastAPI app that accepts resume PDFs, extracts skills with spaCy/Gemini, and scores them against job descriptions stored in ChromaDB.",
      "why_this_project": "Directly demonstrates RAG, LLM integration, and API design — the 3 most asked-about skills for AI Engineer roles at product companies.",
      "skills_demonstrated": ["FastAPI", "ChromaDB", "Gemini API", "Docker", "Python"],
      "skills_learned": ["Vector embeddings", "Prompt engineering", "Async Python"],
      "estimated_time": "2-3 weeks",
      "difficulty": "intermediate",
      "tech_stack": {
        "backend":   ["FastAPI", "Python", "PostgreSQL"],
        "ai":        ["Gemini API", "LangChain", "ChromaDB"],
        "devops":    ["Docker", "GitHub Actions"]
      },
      "github_readme_sections": ["Problem Statement", "Architecture Diagram", "Tech Stack", "Setup", "API Docs", "Screenshots", "Future Improvements"],
      "interview_talking_points": [
        "How you designed the embedding pipeline",
        "Why ChromaDB over Pinecone",
        "How you handled resume parsing edge cases"
      ],
      "similar_roles_impressed": ["AI Engineer", "ML Engineer", "Backend Engineer"]
    }
  ],
  "projects_to_avoid": ["Basic todo app", "Weather app", "Calculator — already very common"],
  "portfolio_score": 45,
  "portfolio_target": 80
}
```

### LangGraph Integration

**Node name:** `AgentName.PROJECT_RECOMMENDATION` = `"project_recommendation_agent"` (add to `AgentName`)

**Chaining pattern:** This agent is most valuable when called after **both** Resume Agent and Skill Gap Agent have run — it reads from both their state outputs. The Supervisor should prefer queuing `[RESUME, SKILL_GAP, PROJECT_RECOMMENDATION]` when the user asks "what projects should I build?"

**Supervisor routing trigger phrases:** "what project", "project ideas", "portfolio", "what should I build", "project recommendations", "GitHub projects"

**State reads:** `target_role`, `resume_analysis`, `skill_gap_analysis`  
**State writes:** `project_recommendations_output`

### ChromaDB Collections Required

**New collection: `project_templates`**

| Field | Type | Description |
|---|---|---|
| `document` | string | Project idea with full description |
| `metadata.role_category` | string | "ai_ml" \| "backend" \| "frontend" \| "fullstack" \| "data" |
| `metadata.difficulty` | string | "beginner" \| "intermediate" \| "advanced" |
| `metadata.primary_skill` | string | Main skill demonstrated |
| `metadata.time_weeks` | int | Estimated weeks to complete |
| `metadata.industry` | string | "fintech" \| "healthtech" \| "general" \| "edtech" |

**Seed content needed:**
- 150+ project templates across 8 role categories
- Each template: description, tech stack, interview value, difficulty
- Anti-patterns: list of overused projects to avoid

### API Endpoints Required

```
POST /api/projects/recommend
     Body: { "experience_level": str, "time_available_weeks": int }
     Response: ProjectRecommendationResponse

GET  /api/projects/saved
     Response: user's saved/bookmarked projects

POST /api/projects/{project_id}/save
     Response: 204 No Content

GET  /api/projects/portfolio-score
     Response: { "score": int, "breakdown": {...}, "suggestions": [...] }
```

### Database Schema Changes

**New table: `project_recommendations`**

```sql
CREATE TABLE project_recommendations (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_role      VARCHAR(100),
    experience_level VARCHAR(20),
    recommendations  JSONB,        -- full list of recommended projects
    portfolio_score  INTEGER,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE saved_projects (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_title  VARCHAR(200) NOT NULL,
    project_data   JSONB,
    status         VARCHAR(20) DEFAULT 'saved',  -- 'saved' | 'in_progress' | 'completed'
    saved_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_project_recommendations_user_id ON project_recommendations(user_id);
CREATE INDEX ix_saved_projects_user_id ON saved_projects(user_id);
```

**`career_scores` table: add `project_score INTEGER` column**

### Estimated Implementation Effort

| Task | Effort |
|---|---|
| `project_recommendation_agent.py` | 2 days |
| `project_recommendation_prompts.py` | 1 day |
| `project_recommendation_service.py` | 0.5 days |
| `schemas/project.py` | 0.5 days |
| `api/routes/projects.py` (4 endpoints) | 1 day |
| ChromaDB seed data (150+ templates) | 3 days |
| `graph.py` + Supervisor update | 0.5 days |
| Frontend: Project Recommendations page | 2.5 days |
| **Total** | **~11 days** |

---

## Agent 4 — LinkedIn Optimization Agent

### Responsibilities

Analyzes and rewrites LinkedIn profile sections to maximise discoverability, recruiter appeal, and ATS compatibility for the user's target role. Takes the user's current LinkedIn content (pasted as text) and generates optimised versions of: Headline, About/Summary, Skills section (ordered by relevance), Experience bullet points (STAR-format rewrite), and Featured section suggestions. Also generates a list of people/communities to follow and posts to engage with.

Unlike the Resume Agent (which scores PDFs), this agent works on raw text input and focuses on LinkedIn-specific optimisation mechanics: keyword density for LinkedIn search, engagement hooks in the About section, creator economy tactics.

### Inputs

| Input | Source | Description |
|---|---|---|
| `linkedin_headline` | API request | Current headline text |
| `linkedin_about` | API request | Current About/Summary section |
| `linkedin_experience` | API request | Experience section text |
| `linkedin_skills` | API request | Current skills list |
| `target_role` | `state["target_role"]` | Role to optimise toward |
| `resume_analysis` | `state["resume_analysis"]` | Skills and strengths from resume (if available) |
| `skill_gap_analysis` | `state["skill_gap_analysis"]` | Skills to highlight (if available) |

### Outputs

State field: `linkedin_optimization_output: dict`

```json
{
  "current_score": 58,
  "optimized_score": 87,
  "sections": {
    "headline": {
      "current":   "B.Tech CSE | Looking for opportunities",
      "optimized": "AI Engineer | LangChain · FastAPI · LLMs | Building production AI systems",
      "reasoning": "Includes searchable keywords. Role-first structure. Demonstrates specialization."
    },
    "about": {
      "current":   "I am a fresher looking for opportunities in AI...",
      "optimized": "I build AI systems that actually ship to production...\n[full rewritten 300-word about]",
      "hook_score": 82
    },
    "skills_reorder": {
      "recommended_order": ["Python", "LangChain", "FastAPI", "Machine Learning", "SQL"],
      "skills_to_add": ["Prompt Engineering", "RAG", "Vector Databases"],
      "skills_to_remove": ["Microsoft Word", "Teamwork"]
    },
    "experience_rewrites": [
      {
        "original":  "Worked on ML project during internship",
        "rewritten": "Developed a text classification pipeline using BERT fine-tuning (HuggingFace) achieving 94% accuracy on 50k customer support tickets, reducing manual triage time by 40%",
        "star_format": true
      }
    ],
    "featured_section": ["Pin your best GitHub project", "Pin a post about your AI project journey"],
    "creator_tips": ["Post 1x/week about your learning journey", "Comment on posts by target company recruiters"],
    "follow_suggestions": ["Roles to follow", "Communities to join", "Hashtags to use"]
  },
  "keyword_density": {
    "ai_engineer_keywords_present": ["Python", "Machine Learning"],
    "missing_high_value_keywords":  ["MLOps", "LLMOps", "Retrieval Augmented Generation"]
  }
}
```

### LangGraph Integration

**Node name:** `AgentName.LINKEDIN` = `"linkedin_agent"` (already declared in Phase 1 `AgentName`)

**Standalone nature:** LinkedIn optimization often runs independently (user wants to fix their profile, not necessarily related to resume/skills). Supervisor should support both standalone and chained invocation.

**Supervisor routing trigger phrases:** "LinkedIn", "optimize my profile", "LinkedIn headline", "improve my summary", "LinkedIn about section", "recruiter visibility"

**State reads:** `target_role`, `resume_analysis`, `skill_gap_analysis`  
**State writes:** `linkedin_optimization_output`

### ChromaDB Collections Required

**New collection: `linkedin_templates`**

| Field | Type | Description |
|---|---|---|
| `document` | string | Example headlines, about sections, bullet points |
| `metadata.section_type` | string | "headline" \| "about" \| "experience" \| "skills" |
| `metadata.role_category` | string | "ai_ml" \| "backend" \| "data" \| "product" |
| `metadata.experience_level` | string | "fresher" \| "mid" \| "senior" |
| `metadata.engagement_score` | int | 0-100, how well this template performs |

**Seed content needed:**
- 50 headline templates per role category
- 20 full About section examples per role
- 100 STAR-format experience bullet templates
- Keyword lists per role (for density checking)
- Anti-pattern examples (what NOT to write)

### API Endpoints Required

```
POST /api/linkedin/optimize
     Body: { "headline": str, "about": str, "experience": str, "skills": list[str] }
     Response: LinkedInOptimizationResponse

GET  /api/linkedin/score
     Body: same as above
     Response: { "score": int, "breakdown": {...} }

GET  /api/linkedin/history
     Response: list of past optimization sessions

GET  /api/linkedin/keywords?role=ai-engineer
     Response: high-value keywords for that role
```

### Database Schema Changes

**New table: `linkedin_optimizations`**

```sql
CREATE TABLE linkedin_optimizations (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_data      JSONB,   -- { headline, about, experience, skills }
    optimized_data     JSONB,   -- full LinkedInOptimizationOutput
    current_score      INTEGER,
    optimized_score    INTEGER,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_linkedin_optimizations_user_id ON linkedin_optimizations(user_id);
```

**`career_scores` table: add `linkedin_score INTEGER` column**

### Estimated Implementation Effort

| Task | Effort |
|---|---|
| `linkedin_agent.py` | 2 days |
| `linkedin_prompts.py` | 1 day |
| `linkedin_service.py` | 0.5 days |
| `schemas/linkedin.py` | 0.5 days |
| `api/routes/linkedin.py` (4 endpoints) | 1 day |
| ChromaDB seed data (templates + keywords) | 2 days |
| `graph.py` + Supervisor update | 0.5 days |
| Frontend: LinkedIn Optimizer page | 3 days |
| **Total** | **~10.5 days** |

---

## Agent 5 — Spoken English Agent

### Responsibilities

Evaluates and improves the user's spoken/written English specifically for professional contexts: interviews, presentations, emails, and client calls. The user provides a voice note transcript or typed paragraph (e.g. their answer to "Tell me about yourself"). The agent evaluates: grammar, fluency, filler word usage, answer structure (STAR format compliance), professional vocabulary, conciseness, and confidence signals. Returns a corrected version with line-by-line annotations explaining every change.

Also generates practice scripts: 30-second elevator pitch, 2-minute "tell me about yourself", answers to 10 most common HR questions — all tailored to the user's actual background from resume data.

**Important scope boundary:** This agent works on text. Audio-to-text conversion (Whisper or similar) is a frontend concern — the backend receives transcripts.

### Inputs

| Input | Source | Description |
|---|---|---|
| `spoken_text` | API request | Transcript of what the user said / typed answer |
| `context_type` | API request | "interview_answer" \| "self_intro" \| "email" \| "presentation" |
| `question` | API request | The question being answered (for structure evaluation) |
| `resume_analysis` | `state["resume_analysis"]` | User's background for personalised scripts |
| `target_role` | `state["target_role"]` | For vocabulary calibration |

### Outputs

State field: `spoken_english_output: dict`

```json
{
  "original_text": "So basically I am uh a developer who like works on Python and stuff...",
  "corrected_text": "I'm a Python developer with 2 years of experience building backend APIs...",
  "scores": {
    "grammar":      72,
    "fluency":      65,
    "structure":    58,
    "vocabulary":   70,
    "conciseness":  60,
    "overall":      65
  },
  "issues": [
    { "type": "filler_word",   "found": "uh",    "suggestion": "Remove — pause instead" },
    { "type": "filler_phrase", "found": "and stuff", "suggestion": "Be specific: name the actual technologies" },
    { "type": "grammar",       "found": "I am developer", "suggestion": "I'm a developer" },
    { "type": "structure",     "issue": "Missing impact statement", "suggestion": "End with a result: 'reduced load time by 40%'" }
  ],
  "annotations": [
    { "original": "basically", "corrected": "[removed]", "reason": "Filler — weakens professional impression" }
  ],
  "star_compliance": {
    "situation": true,
    "task":      false,
    "action":    true,
    "result":    false,
    "score":     50,
    "tip": "Add the measurable result of your action"
  },
  "practice_scripts": {
    "elevator_pitch_30s": "...personalised 30s pitch...",
    "self_intro_2min":    "...personalised 2min intro...",
    "sample_hr_answers": {
      "tell_me_about_yourself":    "...",
      "greatest_strength":         "...",
      "where_do_you_see_yourself": "..."
    }
  },
  "vocabulary_upgrades": [
    { "weak": "I worked on",   "strong": "I engineered / I architected / I led" },
    { "weak": "I helped with", "strong": "I contributed to / I was responsible for" }
  ]
}
```

### LangGraph Integration

**Node name:** `AgentName.SPOKEN_ENGLISH` = `"spoken_english_agent"` (already declared in Phase 1 `AgentName`)

**Standalone nature:** Frequently called independently. Can also chain after Interview Agent — user gets interview questions, answers them, and immediately gets English evaluation.

**Supervisor routing trigger phrases:** "improve my English", "check my answer", "how do I sound", "evaluate my response", "grammar check", "practice self introduction", "tell me about yourself practice"

**State reads:** `target_role`, `resume_analysis`  
**State writes:** `spoken_english_output`

### ChromaDB Collections Required

**New collection: `english_templates`**

| Field | Type | Description |
|---|---|---|
| `document` | string | Example answers, vocabulary lists, grammar patterns |
| `metadata.template_type` | string | "hr_answer" \| "elevator_pitch" \| "vocab_upgrade" \| "filler_words" |
| `metadata.context` | string | "interview" \| "email" \| "presentation" |
| `metadata.proficiency_target` | string | "professional" \| "advanced" |
| `metadata.role_category` | string | "technical" \| "non_technical" \| "general" |

**Seed content needed:**
- 200 strong vs weak vocabulary pairs
- 50 model HR question answers
- STAR format examples
- Common Indian English grammar mistakes and corrections
- Filler word list with replacements
- 20 elevator pitch templates by role

### API Endpoints Required

```
POST /api/english/evaluate
     Body: { "spoken_text": str, "context_type": str, "question": str }
     Response: SpokenEnglishResponse

POST /api/english/generate-scripts
     Body: { "script_types": list[str] }
     Response: { "scripts": { "elevator_pitch": str, ... } }

GET  /api/english/vocabulary?role=ai-engineer
     Response: vocabulary upgrade list for that role

GET  /api/english/history
     Response: past evaluation sessions with score trend
```

### Database Schema Changes

**New table: `english_evaluations`**

```sql
CREATE TABLE english_evaluations (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_text     TEXT NOT NULL,
    corrected_text    TEXT,
    context_type      VARCHAR(30),
    overall_score     INTEGER,
    scores_breakdown  JSONB,
    issues            JSONB,
    practice_scripts  JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_english_evaluations_user_id ON english_evaluations(user_id);
```

### Estimated Implementation Effort

| Task | Effort |
|---|---|
| `spoken_english_agent.py` | 2 days |
| `spoken_english_prompts.py` (complex prompts) | 1.5 days |
| `spoken_english_service.py` | 0.5 days |
| `schemas/english.py` | 0.5 days |
| `api/routes/english.py` (4 endpoints) | 1 day |
| ChromaDB seed data (vocab, templates) | 2 days |
| `graph.py` + Supervisor update | 0.5 days |
| Frontend: English Evaluator page | 3 days |
| **Total** | **~11 days** |

---

## Agent 6 — Wellness & Motivation Agent

### Responsibilities

The only non-technical agent. Provides personalized motivation, burnout detection, study schedule accountability, and stress management during the job search / preparation journey. Takes emotional check-in messages ("I failed 3 interviews and feel like giving up") and responds with: validated emotional support, reframed perspective, concrete next step (one specific action), and optional study schedule adjustment.

Also generates weekly motivational messages based on the user's progress data (career score trend, quizzes completed, applications sent). Detects patterns in progress data that signal burnout risk and proactively suggests rest/recovery.

**Important scope boundary:** This is career-context wellness, not mental health therapy. The agent always suggests professional help for serious mental health concerns and never attempts to diagnose or treat. Tone is that of an experienced mentor, not a therapist.

### Inputs

| Input | Source | Description |
|---|---|---|
| `mood_message` | API request | User's free-text emotional check-in |
| `progress_data` | API request / DB | Career score history, sessions completed, streak |
| `recent_activity` | DB query | Last 7 days of quiz scores, interview attempts |
| `target_role` | `state["target_role"]` | For context-aware motivation |

### Outputs

State field: `wellness_output: dict`

```json
{
  "emotional_validation": "Three interview rejections is genuinely hard, and it's completely normal to feel discouraged at this point in the process.",
  "reframe": "Each rejection is a calibration signal, not a verdict on your ability. The people who eventually land roles are the ones who treat rejection as data.",
  "next_single_action": "Today, do just one thing: spend 20 minutes reviewing the one question you found hardest in your last interview. Just one question. That's it.",
  "progress_acknowledgment": "You've completed 8 quizzes this week and your Python score went from 60 to 74. That's real, measurable growth.",
  "burnout_risk": {
    "level": "medium",
    "signals": ["Score plateau for 5 days", "3 failed attempts in a row", "No sessions in last 2 days"],
    "recommendation": "Take a 1-day break tomorrow. Rest is part of preparation."
  },
  "motivational_quote": "...",
  "weekly_reflection_prompt": "What's one thing you learned this week that you didn't know before?",
  "adjusted_study_plan": {
    "recommendation": "Reduce daily target from 4 hours to 2 hours for the next 3 days",
    "reason": "Recovery prevents long-term burnout"
  },
  "professional_help_note": null  -- set if serious mental health signals detected
}
```

### LangGraph Integration

**Node name:** `AgentName.WELLNESS` = `"wellness_agent"` (already declared in Phase 1 `AgentName`)

**Standalone nature:** Almost always called independently. Rarely chained with technical agents. However, the Supervisor can proactively chain it if a user's message contains frustration alongside a technical request ("I keep failing interviews, can you give me more questions to practice?").

**Supervisor routing trigger phrases:** "feeling discouraged", "want to give up", "failed interview", "stressed", "burnout", "motivate me", "feeling stuck", "demotivated", "how long will this take", "is this worth it"

**Sensitive content handling:** This agent's Gemini prompt must explicitly instruct the LLM to:
- Never dismiss or minimize emotional distress
- Always recommend professional help if user mentions self-harm, severe depression, or crisis
- Maintain warmth without overstepping into therapy

**State reads:** `target_role`, `user_id` (to query progress from DB)  
**State writes:** `wellness_output`

### ChromaDB Collections Required

**New collection: `wellness_content`**

| Field | Type | Description |
|---|---|---|
| `document` | string | Motivational frameworks, reframing techniques |
| `metadata.content_type` | string | "reframe" \| "quote" \| "strategy" \| "crisis_resource" |
| `metadata.situation` | string | "rejection" \| "plateau" \| "comparison" \| "imposter_syndrome" \| "burnout" |
| `metadata.tone` | string | "empathetic" \| "direct" \| "gentle" |

**Seed content needed:**
- 100 reframing techniques for 10 common job-search situations
- 50 motivational frameworks (Growth Mindset, Stoic practices for career)
- Study schedule recovery templates
- Crisis resource references (iCall India, Vandrevala Foundation)
- Weekly reflection prompts (52 weeks)

### API Endpoints Required

```
POST /api/wellness/checkin
     Body: { "mood_message": str }
     Response: WellnessResponse

GET  /api/wellness/weekly-summary
     Response: weekly progress summary with motivational message

POST /api/wellness/burnout-check
     Body: { "recent_activity_days": int }
     Response: { "burnout_risk": str, "recommendation": str }

GET  /api/wellness/history
     Response: past check-in sessions
```

### Database Schema Changes

**New table: `wellness_checkins`**

```sql
CREATE TABLE wellness_checkins (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mood_message           TEXT,
    burnout_risk_level     VARCHAR(10),  -- 'low' | 'medium' | 'high'
    response_data          JSONB,        -- full WellnessOutput
    professional_help_flag BOOLEAN DEFAULT false,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_wellness_checkins_user_id ON wellness_checkins(user_id);
```

**Note:** No PII concern beyond what's already in the DB. The `professional_help_flag` allows monitoring for at-risk users if the platform adds moderation later.

### Estimated Implementation Effort

| Task | Effort |
|---|---|
| `wellness_agent.py` | 1.5 days |
| `wellness_prompts.py` (sensitivity requires extra care) | 1.5 days |
| `wellness_service.py` + burnout detection logic | 1 day |
| `schemas/wellness.py` | 0.5 days |
| `api/routes/wellness.py` (4 endpoints) | 1 day |
| ChromaDB seed data (reframes, resources) | 1.5 days |
| `graph.py` + Supervisor update | 0.5 days |
| Frontend: Wellness Check-in page | 2 days |
| **Total** | **~9.5 days** |

---

## Cross-Cutting Changes Required

These changes affect files that are shared across all agents. They are done **once** for all 6 Phase 2 agents together.

### 1. `app/agents/state.py` — New state fields

Add the following fields to `CareerCopilotState`:

```python
# ── Phase 2 Agent Outputs ──────────────────────────────────────────────────────
company_research_output:        dict[str, Any]
internship_research_output:     dict[str, Any]
project_recommendations_output: dict[str, Any]
linkedin_optimization_output:   dict[str, Any]
spoken_english_output:          dict[str, Any]
wellness_output:                dict[str, Any]

# ── Phase 2 Inputs ─────────────────────────────────────────────────────────────
company_name:        str   # For Company Research Agent
spoken_text:         str   # For Spoken English Agent
linkedin_profile:    dict  # For LinkedIn Agent (headline, about, experience, skills)
mood_message:        str   # For Wellness Agent
experience_level:    str   # For Project Recommendation + Internship Agent
education_level:     str   # For Internship Research Agent
```

Update `create_initial_state()` factory to include all new fields with appropriate defaults.

Update `AgentName` class:
```python
INTERNSHIP_RESEARCH     = "internship_research_agent"
PROJECT_RECOMMENDATION  = "project_recommendation_agent"

PHASE_2_AGENTS: list[str] = [
    COMPANY_RESEARCH,
    INTERNSHIP_RESEARCH,
    PROJECT_RECOMMENDATION,
    LINKEDIN,
    SPOKEN_ENGLISH,
    WELLNESS,
]
```

### 2. `app/agents/graph.py` — Node registration

```python
# Import all Phase 2 agents (with stub fallbacks, same as Phase 1 pattern)
from app.agents.company.company_research_agent    import company_research_agent_node
from app.agents.company.internship_research_agent import internship_research_agent_node
from app.agents.personal.project_recommendation_agent import project_recommendation_agent_node
from app.agents.personal.linkedin_agent           import linkedin_agent_node
from app.agents.personal.spoken_english_agent     import spoken_english_agent_node
from app.agents.personal.wellness_agent           import wellness_agent_node

# In build_graph():
graph.add_node(AgentName.COMPANY_RESEARCH,       company_research_agent_node)
graph.add_node(AgentName.INTERNSHIP_RESEARCH,    internship_research_agent_node)
graph.add_node(AgentName.PROJECT_RECOMMENDATION, project_recommendation_agent_node)
graph.add_node(AgentName.LINKEDIN,               linkedin_agent_node)
graph.add_node(AgentName.SPOKEN_ENGLISH,         spoken_english_agent_node)
graph.add_node(AgentName.WELLNESS,               wellness_agent_node)

# Extend conditional edges to include all Phase 2 agents
# Extend PHASE_2_AGENTS loop for post-agent routing
```

**New agent directory structure:**
```
backend/app/agents/
├── career/          (Phase 1 — unchanged)
├── interview/       (Phase 1 — unchanged)
├── personal/        (Phase 1: study_planner + Phase 2: linkedin, project, english, wellness)
│   ├── study_planner_agent.py      ← existing
│   ├── linkedin_agent.py           ← new
│   ├── project_recommendation_agent.py  ← new
│   ├── spoken_english_agent.py     ← new
│   └── wellness_agent.py           ← new
└── company/         (new directory)
    ├── __init__.py
    ├── company_research_agent.py   ← new
    └── internship_research_agent.py ← new
```

### 3. `app/agents/supervisor.py` — Routing table extension

The Supervisor's system prompt needs to be extended with routing rules for all 6 new agents. The valid agent names in the prompt JSON schema expand from 5 to 11. No other changes to supervisor logic — same Gemini Flash model, same parsing function.

### 4. `app/rag/chromadb_client.py` — New collection names

```python
class CollectionName:
    # Phase 1 (unchanged)
    INTERVIEW_QUESTIONS = "interview_questions"
    LEARNING_RESOURCES  = "learning_resources"
    COMPANY_INFO        = "company_info"
    CAREER_GUIDANCE     = "career_guidance"
    JOB_REQUIREMENTS    = "job_requirements"

    # Phase 2 (new)
    COMPANY_PROFILES    = "company_profiles"       # Agent 1
    INTERNSHIP_PROGRAMS = "internship_programs"    # Agent 2
    PROJECT_TEMPLATES   = "project_templates"      # Agent 3
    LINKEDIN_TEMPLATES  = "linkedin_templates"     # Agent 4
    ENGLISH_TEMPLATES   = "english_templates"      # Agent 5
    WELLNESS_CONTENT    = "wellness_content"       # Agent 6
```

### 5. `app/rag/retriever.py` — Collection routing map

Extend `_agent_to_collection()` mapping:

```python
AgentName.COMPANY_RESEARCH:       CollectionName.COMPANY_PROFILES,
AgentName.INTERNSHIP_RESEARCH:    CollectionName.INTERNSHIP_PROGRAMS,
AgentName.PROJECT_RECOMMENDATION: CollectionName.PROJECT_TEMPLATES,
AgentName.LINKEDIN:               [CollectionName.LINKEDIN_TEMPLATES, CollectionName.JOB_REQUIREMENTS],
AgentName.SPOKEN_ENGLISH:         CollectionName.ENGLISH_TEMPLATES,
AgentName.WELLNESS:               CollectionName.WELLNESS_CONTENT,
```

### 6. `app/scoring/career_readiness.py` — Weight redistribution

```python
# Phase 2 weights (redistribute to include linkedin + project)
WEIGHTS = {
    "resume_score":    0.25,   # was 0.30
    "skill_score":     0.20,   # was 0.25
    "quiz_score":      0.20,   # was 0.25
    "interview_score": 0.20,   # unchanged
    "linkedin_score":  0.10,   # new
    "project_score":   0.05,   # new
}
```

`CareerReadinessScore` dataclass gains `linkedin_score: int = 0` and `project_score: int = 0`.

### 7. `app/db/migrations/versions/` — New migration files

```
0002_phase2_tables.py      — 6 new tables + columns on users/career_scores
0003_users_education.py    — education_level, college_name on users table
```

### 8. `app/models/models.py` — New ORM models

One new `Base` subclass per new table (6 models). Add relationships to `User` model with `back_populates`. Follow exact same pattern as Phase 1 models.

---

## Phase 2 Implementation Order

The recommended build sequence to maximise testability and avoid blocking dependencies:

```
Week 1-2:   Cross-cutting changes (state.py, graph.py, chromadb, retriever, scoring)
            → All 6 agents have their "scaffolding" in place before any is implemented

Week 3-4:   Company Research Agent + API + seed data
            → First agent to validate the new pattern end-to-end

Week 5:     Internship Research Agent + API + seed data
            → Reuses company research pattern; faster second agent

Week 6-7:   Project Recommendation Agent + API + seed data (largest seed effort)

Week 8:     LinkedIn Optimization Agent + API + seed data

Week 9-10:  Spoken English Agent + API + seed data

Week 11:    Wellness Agent + API + seed data (most sensitive — extra prompt review)

Week 12:    Frontend pages for all 6 agents + integration testing
            Career Score weight redistribution + Dashboard Phase 2 components
```

---

## Total Effort Summary

| Agent | Backend | Seed Data | Frontend | Total |
|---|---|---|---|---|
| Company Research | 4 days | 2 days | 2 days | 8 days |
| Internship Research | 3.5 days | 1.5 days | 2 days | 7 days |
| Project Recommendation | 4.5 days | 3 days | 2.5 days | 10 days |
| LinkedIn Optimization | 4.5 days | 2 days | 3 days | 9.5 days |
| Spoken English | 4.5 days | 2 days | 3 days | 9.5 days |
| Wellness & Motivation | 4.5 days | 1.5 days | 2 days | 8 days |
| Cross-cutting changes | 3 days | — | 1 day | 4 days |
| **TOTAL** | **29 days** | **12 days** | **15.5 days** | **~56 days** |

**Realistic timeline with 1 developer:** 10-12 weeks  
**With 2 developers (backend + frontend in parallel):** 6-7 weeks

---

## What Does NOT Change in Phase 2

The following Phase 1 components require zero modification:

- `app/core/security.py` — JWT/auth unchanged
- `app/api/routes/auth.py` — no auth changes
- `app/db/database.py` — DB engine unchanged
- `app/llm/gemini_client.py` — same Gemini Flash client
- `app/agents/router.py` — `route_after_agent()` works for any agent generically
- `app/agents/synthesizer.py` — synthesizes any agent output already
- `app/services/pdf_service.py` — PDF parsing unchanged
- All Phase 1 agents — zero changes to resume, skill_gap, interview, quiz, study_planner
- All Phase 1 API routes — existing endpoints unaffected
- `docker-compose.yml` — no infrastructure changes needed
- `frontend/src/stores/authStore.ts` — auth store unchanged

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Gemini Flash rate limit hit with 11 agents | High | Medium | Add per-agent rate limit monitoring; use Groq for high-volume English eval |
| ChromaDB performance with 11 collections | Low | Medium | Already using `run_in_executor` (Phase 1 fix); monitor query times |
| Wellness Agent prompt safety violations | Medium | High | Test 50+ edge case inputs before shipping; add profanity/crisis filter layer |
| Seed data quality for Company Profiles | High | High | Manual review of all 20 company profiles; 2-week buffer in timeline |
| Career score weight redistribution breaks existing user scores | Low | Medium | Migration script to recompute all historical scores with new weights |
| LangGraph state size growth with 11 agent outputs | Low | Low | State is checkpointed to PostgreSQL; no memory concern |

---

*Document prepared based on full audit of Phase 1 codebase. All file paths, class names, and patterns reference the actual implemented code.*
