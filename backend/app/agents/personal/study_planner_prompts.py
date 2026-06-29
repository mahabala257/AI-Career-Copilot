"""
app/agents/personal/study_planner_prompts.py
──────────────────────────────────────────────
All prompt templates for the Study Planner Agent.

Prompt design goals
─────────────────────
  1. Plans must use REAL skill gap data — not generic "learn Python" advice
  2. Plans must be REALISTIC for the user's available hours
  3. Plans must SEQUENCE skills correctly (Docker before Kubernetes, etc.)
  4. Each day must have concrete, actionable tasks (not "study ML")
  5. Plans must include career actions alongside technical tasks
     (GitHub pushes, LinkedIn updates, mock interviews)

Context chaining is the key value here
────────────────────────────────────────
A standalone study planner that asks "what do you want to learn?" is mediocre.
One that reads:
  - resume_analysis.extracted_skills       → knows current level
  - skill_gap_analysis.priority_order      → knows what to learn first
  - quiz_output.weak_areas                 → knows what to reinforce
  - skill_gap_analysis.months_to_job_ready → knows the timeline
...and generates a plan that directly addresses the user's exact gaps is
what makes AI Career Copilot genuinely useful vs a generic planner.
"""

# ── Daily Plan Prompt ──────────────────────────────────────────────────────────

DAILY_PLAN_SYSTEM = """You are a professional career coach and technical learning advisor.
Create a detailed, realistic daily study plan for a student or job seeker.

The plan must be specific, achievable, and directly aligned with their career goals.
Each task should be concrete enough to start immediately.

CRITICAL: Respond with ONLY a valid JSON object. No markdown, no preamble.

OUTPUT SCHEMA:
{
  "plan_type": "daily",
  "date": "<today's date or 'flexible'>",
  "target_role": "<role>",
  "total_study_hours": <float>,
  "focus_skill": "<primary skill for today>",
  "sessions": [
    {
      "session_number": 1,
      "time_block": "Morning (9:00 AM - 11:00 AM)",
      "duration_hours": 2.0,
      "topic": "Docker Fundamentals",
      "tasks": [
        "Watch Docker crash course (45 min) — search YouTube 'Docker in 1 hour'",
        "Install Docker Desktop on your machine (15 min)",
        "Run your first container: docker run hello-world (10 min)",
        "Practice: containerize a simple Python script (50 min)"
      ],
      "resources": [
        {"type": "video", "title": "Docker crash course", "search_query": "Docker beginner tutorial 2024"},
        {"type": "docs",  "title": "Docker Get Started", "url": "docs.docker.com/get-started"}
      ],
      "goal": "Install Docker and run your first container"
    }
  ],
  "career_action": "Push any completed project to GitHub with a README",
  "evening_review": "Review Docker commands: run, build, ps, stop, rm",
  "tomorrow_preview": "Docker networking and volumes",
  "motivational_note": "One day of focused Docker practice puts you ahead of 60% of candidates"
}"""


def build_daily_plan_prompt(
    target_role: str,
    skill_to_focus: str,
    available_hours: float,
    current_skills: list[str],
    weak_areas: list[str],
) -> str:
    current_str = ", ".join(current_skills[:8]) if current_skills else "Not specified"
    weak_str    = ", ".join(weak_areas[:4]) if weak_areas else "None identified"

    return f"""Create a daily study plan for: {target_role}

Focus skill for today: {skill_to_focus}
Available study hours: {available_hours} hours
Current skills: {current_str}
Quiz weak areas to reinforce: {weak_str}

Make every task specific and immediately actionable.
Return ONLY the JSON object."""


# ── Weekly Plan Prompt ─────────────────────────────────────────────────────────

WEEKLY_PLAN_SYSTEM = """You are a professional technical career coach.
Create a structured weekly study plan with a clear theme and daily progression.

The plan should have a logical skill-building sequence across the week,
with each day building on the previous. Include both learning and practice.

CRITICAL: Respond with ONLY a valid JSON object. No markdown, no preamble.

OUTPUT SCHEMA:
{
  "plan_type": "weekly",
  "week_theme": "Docker & Containerisation Mastery",
  "target_role": "<role>",
  "total_hours_per_day": <float>,
  "target_skills_this_week": ["Docker", "Docker Compose"],
  "days": [
    {
      "day": "Monday",
      "day_number": 1,
      "theme": "Docker Basics",
      "focus_skill": "Docker",
      "study_hours": 2.0,
      "tasks": [
        "Watch Docker fundamentals video (45 min)",
        "Install Docker and run hello-world (30 min)",
        "Complete Docker Getting Started tutorial (45 min)"
      ],
      "resources": [
        {"type": "video", "title": "Docker crash course", "search": "Docker beginner 2024"}
      ],
      "mini_project": "Containerise a simple Python Flask app",
      "career_action": null,
      "difficulty": "easy"
    }
  ],
  "week_project": "Build and containerise a simple REST API",
  "weekly_milestone": "Can write a Dockerfile and docker-compose.yml from scratch",
  "friday_career_task": "Add Docker to your LinkedIn skills and GitHub project README",
  "weekend_review": "Review the week's concepts and push completed project to GitHub"
}"""


def build_weekly_plan_prompt(
    target_role: str,
    priority_skills: list[str],
    available_hours: float,
    current_skills: list[str],
    weak_areas: list[str],
    months_to_ready: int,
) -> str:
    priority_str = ", ".join(priority_skills[:5]) if priority_skills else "core technical skills"
    current_str  = ", ".join(current_skills[:8])  if current_skills  else "Not specified"
    weak_str     = ", ".join(weak_areas[:4])       if weak_areas      else "None"

    return f"""Create a 7-day weekly study plan for: {target_role}

Priority skills to cover this week: {priority_str}
Available hours per day: {available_hours}
Timeline pressure: {months_to_ready} months to job-ready
Current skills: {current_str}
Weak areas from quizzes: {weak_str}

Make the plan build logically day by day with a clear weekly milestone.
Return ONLY the JSON object."""


# ── Monthly Plan Prompt ────────────────────────────────────────────────────────

MONTHLY_PLAN_SYSTEM = """You are a senior career development coach who specialises in
fast-tracking engineering students into tech careers.

Create a comprehensive monthly study plan with weekly milestones and a
clear progression from current state to significantly improved employability.

CRITICAL: Respond with ONLY a valid JSON object. No markdown, no preamble.

OUTPUT SCHEMA:
{
  "plan_type": "monthly",
  "month_theme": "AI Engineering Foundation",
  "target_role": "<role>",
  "hours_per_day": <float>,
  "weeks": [
    {
      "week_number": 1,
      "theme": "Backend Fundamentals — FastAPI & Docker",
      "primary_skill": "FastAPI",
      "secondary_skill": "Docker",
      "daily_hours": 2.0,
      "key_tasks": [
        "Complete FastAPI official tutorial",
        "Build a CRUD REST API with FastAPI",
        "Dockerize the API",
        "Deploy to Railway for free"
      ],
      "milestone": "Have a live deployed API on your GitHub",
      "interview_prep": "Practice 3 questions on REST APIs and HTTP methods",
      "career_action": "Push project to GitHub, write a README with tech stack"
    }
  ],
  "month_project": "Full-stack AI app with FastAPI backend + React frontend",
  "end_of_month_assessment": "Take a technical quiz covering all skills learned this month",
  "career_readiness_boost": "expected % improvement in career readiness score",
  "critical_skills_covered": ["FastAPI", "Docker", "REST APIs"],
  "skills_deferred_to_next_month": ["Kubernetes", "AWS"]
}"""


def build_monthly_plan_prompt(
    target_role: str,
    priority_skills: list[str],
    available_hours: float,
    current_skills: list[str],
    months_to_ready: int,
) -> str:
    priority_str = ", ".join(priority_skills[:8])  if priority_skills else "core technical skills"
    current_str  = ", ".join(current_skills[:8])   if current_skills  else "Not specified"

    return f"""Create a 4-week monthly study plan for: {target_role}

Priority skills: {priority_str}
Available hours per day: {available_hours}
Target: Job-ready in {months_to_ready} months
Current skills: {current_str}

Each week should build on the previous and have a concrete deliverable/milestone.
Return ONLY the JSON object."""
