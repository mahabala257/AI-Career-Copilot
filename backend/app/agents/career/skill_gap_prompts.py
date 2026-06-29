"""
app/agents/career/skill_gap_prompts.py
────────────────────────────────────────
All prompt templates for the Skill Gap Agent.

Prompt design philosophy for skill gap analysis
─────────────────────────────────────────────────
The core challenge: Gemini must produce a STRUCTURED comparison that goes
beyond just listing missing skills. It needs to:

  1. Know what skills are ACTUALLY required for the role (job market context)
  2. Understand the LEVEL of each skill needed (beginner vs production-grade)
  3. Assign a PRIORITY ORDER based on what gives the most career impact first
  4. Give REALISTIC time estimates (not "learn Python in 1 week")
  5. Categorise skills so the frontend can build a roadmap view

The RAG context injection is critical here — without ChromaDB job specs,
Gemini would rely solely on training data for role requirements. With RAG,
we ground the response in the actual job market data we've seeded.

Three prompts:
  1. SKILL_GAP_ANALYSIS_SYSTEM / build_skill_gap_prompt
     → Main analysis: compare current vs required, classify, prioritise

  2. LEARNING_PATH_SYSTEM / build_learning_path_prompt
     → Deep-dive learning path for each missing skill
     → Called optionally when user wants a full roadmap (not just the gap list)

  3. ROADMAP_SYSTEM / build_roadmap_prompt
     → Converts skill gaps into a timeline roadmap (3/6/12 month)
     → Used by the CareerRoadmap page in Phase 2
"""

# ── Main Skill Gap Analysis Prompt ────────────────────────────────────────────

SKILL_GAP_ANALYSIS_SYSTEM = """You are a senior technical career advisor and hiring manager 
with expertise in the AI/ML, software engineering, and data science job market.

Your task is to perform a comprehensive skill gap analysis: compare the candidate's 
current skills against what is genuinely required for their target role, then 
produce a prioritised action plan.

CRITICAL RULES:
1. Respond with ONLY a valid JSON object. No markdown fences, no explanation, no preamble.
2. Be role-specific — "AI Engineer" needs different skills than "Data Scientist".
3. Priority order must be based on hiring market impact, not alphabetical.
4. Time estimates must be realistic for a student studying 2-3 hours/day.
5. Proficiency levels: "aware" (know it exists), "basic" (tutorials done), 
   "intermediate" (built projects), "production" (used in real systems).
6. Never invent skills the candidate has. Only use what is explicitly provided.

OUTPUT SCHEMA (return exactly this structure):
{
  "target_role": "<role name>",
  "overall_readiness_percent": <integer 0-100>,
  "current_skills": ["skill1", "skill2"],
  "required_skills": ["skill1", "skill2"],
  "matched_skills": [
    {"skill": "Python", "candidate_level": "intermediate", "required_level": "production", "gap": "small"}
  ],
  "missing_skills": [
    {
      "skill": "Docker",
      "category": "devops|ml|backend|frontend|data|soft",
      "priority": "critical|high|medium|low",
      "why_important": "one sentence explanation",
      "time_to_learn": "2 weeks",
      "learning_resources": ["Official Docker docs", "Docker in 1 hour - YouTube"]
    }
  ],
  "priority_order": ["skill1", "skill2", "skill3"],
  "skill_categories": {
    "strong": ["skills candidate is good at"],
    "developing": ["skills candidate has but needs to improve"],
    "missing_critical": ["must-learn for the role"],
    "missing_nice_to_have": ["good to have but not blocking"]
  },
  "months_to_job_ready": <integer>,
  "immediate_actions": ["action1", "action2", "action3"],
  "strengths_to_highlight": ["what the candidate should emphasise in interviews"]
}"""


def build_skill_gap_prompt(
    current_skills: list[str],
    target_role: str,
    rag_context: list[str],
    resume_analysis: dict | None = None,
) -> str:
    """
    Build the human-turn message for skill gap analysis.

    Pulls skills from two sources:
      1. Explicitly provided current_skills list (from user profile or state)
      2. resume_analysis["extracted_skills"] if a resume was already analyzed

    This gives the agent the richest possible picture of what the candidate knows.
    """
    # Merge skills from both sources, deduplicate
    all_skills = list(dict.fromkeys(current_skills))  # preserve order, deduplicate
    if resume_analysis and resume_analysis.get("extracted_skills"):
        for skill in resume_analysis["extracted_skills"]:
            if skill and skill not in all_skills:
                all_skills.append(skill)

    skills_str = ", ".join(all_skills) if all_skills else "No skills provided yet"

    rag_section = ""
    if rag_context:
        rag_section = f"""
MARKET CONTEXT — Job Requirements (from knowledge base):
{chr(10).join(f'  • {chunk}' for chunk in rag_context[:6])}
"""

    resume_context = ""
    if resume_analysis and resume_analysis.get("ats_score"):
        resume_context = f"""
RESUME CONTEXT:
  • ATS Score: {resume_analysis.get('ats_score')}/100
  • Experience Level: {resume_analysis.get('experience_level', 'unknown')}
  • Critical Missing (from resume analysis): {', '.join(resume_analysis.get('critical_missing', [])[:5])}
"""

    return f"""Perform a complete skill gap analysis for this candidate.

TARGET ROLE: {target_role}

CANDIDATE'S CURRENT SKILLS:
{skills_str}
{resume_context}{rag_section}
Analyse the gap between current skills and what {target_role} roles actually require
in the current job market. Return ONLY the JSON object."""


# ── Learning Path Prompt (detailed per-skill roadmap) ────────────────────────

LEARNING_PATH_SYSTEM = """You are an expert technical educator who creates structured 
learning paths for software engineers and data scientists.

Given a list of missing skills and a target role, create a detailed, actionable 
learning path for each skill. Be specific about resources, projects, and milestones.

CRITICAL: Respond with ONLY a valid JSON object.

OUTPUT SCHEMA:
{
  "learning_paths": [
    {
      "skill": "Docker",
      "why_critical": "one sentence",
      "estimated_weeks": 2,
      "phases": [
        {
          "phase": 1,
          "title": "Fundamentals",
          "duration": "3 days",
          "tasks": ["Install Docker", "Run first container", "Understand images vs containers"],
          "resources": [
            {"type": "video", "title": "Docker in 1 hour", "url": "youtube.com/..."},
            {"type": "docs", "title": "Official Docker Getting Started", "url": "docs.docker.com"}
          ],
          "milestone": "Can run and manage basic containers"
        }
      ],
      "project_idea": "Dockerize your FastAPI resume analyzer project",
      "interview_questions": ["What is the difference between a container and a VM?"]
    }
  ],
  "suggested_sequence": ["skill1_first", "skill2_second"],
  "total_estimated_weeks": <integer>
}"""


def build_learning_path_prompt(
    missing_skills: list[str],
    target_role: str,
    available_hours_per_day: float = 2.0,
) -> str:
    skills_list = "\n".join(f"  - {s}" for s in missing_skills[:8])  # cap at 8
    return f"""Create detailed learning paths for these missing skills targeting: {target_role}

Missing skills to cover:
{skills_list}

Study capacity: {available_hours_per_day} hours per day.

Make each learning path specific, practical, and achievable for an engineering student.
Return ONLY the JSON object."""


# ── Roadmap Prompt (timeline view: 3/6/12 months) ─────────────────────────────

ROADMAP_SYSTEM = """You are a career coach who builds realistic career development roadmaps.
Create a month-by-month roadmap that takes the candidate from their current state 
to being job-ready for their target role.

CRITICAL: Respond with ONLY a valid JSON object.

OUTPUT SCHEMA:
{
  "roadmap_title": "6-Month AI Engineer Roadmap",
  "target_role": "AI Engineer",
  "total_months": 6,
  "milestones": [
    {
      "month": 1,
      "theme": "Foundation Strengthening",
      "goals": ["Complete Docker fundamentals", "Build first FastAPI project"],
      "skills_to_learn": ["Docker", "FastAPI"],
      "project": "Containerized REST API project",
      "career_action": "Update GitHub with new projects"
    }
  ],
  "final_outcome": "description of candidate state after completing roadmap",
  "interview_ready_by_month": <integer>
}"""


def build_roadmap_prompt(
    missing_skills: list[str],
    target_role: str,
    current_skills: list[str],
    months: int = 6,
) -> str:
    missing_str = ", ".join(missing_skills[:12])
    current_str = ", ".join(current_skills[:10])
    return f"""Build a {months}-month career roadmap for this candidate.

Target Role: {target_role}
Current Skills: {current_str}
Skills to Acquire: {missing_str}

Create a realistic month-by-month plan assuming 2-3 hours of study per day.
Return ONLY the JSON object."""
