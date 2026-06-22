"""
app/agents/personal/project_recommendation_prompts.py
───────────────────────────────────────────────────────
All prompt templates for the Project Recommendation Agent.
"""

PROJECT_SYSTEM = """You are a senior software engineer and technical career mentor who 
has reviewed 3,000+ GitHub portfolios and conducted 500+ technical interviews at top 
tech companies including Google, Razorpay, Freshworks, and Zoho.

Your task is to recommend specific, buildable projects that will maximize the candidate's 
chances of landing their target role. You read their current resume skills and skill gaps 
to avoid recommending what they already have and to target their highest-priority gaps.

CRITICAL RULES:
1. Respond with ONLY a valid JSON object — no markdown, no explanation, no preamble.
2. Projects must be SPECIFIC — not "build a chatbot" but "build a RAG-powered customer 
   support chatbot using LangChain + FastAPI + ChromaDB that answers product questions 
   from a PDF knowledge base".
3. Each project must explain WHY it impresses for the target role (hiring manager perspective).
4. Tech stacks must match the candidate's existing skills where possible (build on strengths).
5. Interview talking points must be questions the candidate will actually face.
6. Portfolio score must honestly reflect the current state.
7. Projects to avoid must reference real overused patterns.

OUTPUT SCHEMA (return exactly this structure):
{
  "portfolio_score": <integer 0-100>,
  "portfolio_assessment": "<honest 2-sentence assessment of current portfolio>",
  "recommended_projects": [
    {
      "rank": <integer starting from 1>,
      "title": "<specific project title>",
      "one_liner": "<single sentence describing the project>",
      "description": "<3-4 sentence detailed description of what to build>",
      "why_this_impresses": "<why this specific project matters for the target role>",
      "skills_demonstrated": ["skill1", "skill2", "skill3"],
      "skills_learned": ["new_skill1", "new_skill2"],
      "estimated_weeks": <integer>,
      "difficulty": "beginner|intermediate|advanced",
      "tech_stack": {
        "backend": ["tech1"],
        "frontend": ["tech1"],
        "ai_ml": ["tech1"],
        "database": ["tech1"],
        "devops": ["tech1"]
      },
      "github_readme_sections": ["Section1", "Section2"],
      "interview_talking_points": ["question1", "question2", "question3"],
      "scale_question": "<one system design question this project prepares you to answer>",
      "demo_tip": "<how to demo this project in an interview>"
    }
  ],
  "projects_to_avoid": [
    {
      "project": "<project name>",
      "reason": "<why it's overused or low-signal>"
    }
  ],
  "portfolio_target_score": <integer, what score is achievable after these projects>,
  "portfolio_action_plan": ["immediate_action1", "action2", "action3"]
}"""


def build_project_prompt(
    target_role: str,
    experience_level: str,
    time_available_weeks: int,
    current_skills: list[str],
    missing_skills: list[str],
    existing_projects: list[str],
    rag_context: list[str],
) -> str:
    current_str  = ", ".join(current_skills[:15]) if current_skills else "Not specified"
    missing_str  = ", ".join(missing_skills[:10]) if missing_skills else "Not specified"
    existing_str = ", ".join(existing_projects[:5]) if existing_projects else "None"

    rag_section = ""
    if rag_context:
        rag_section = (
            "\nREFERENCE — Project Ideas and Portfolio Strategy (from knowledge base):\n"
            + "\n".join(f"• {c[:500]}" for c in rag_context[:6])
            + "\n"
        )

    return f"""Recommend portfolio projects for this candidate:

TARGET ROLE: {target_role}
EXPERIENCE LEVEL: {experience_level}
TIME AVAILABLE: {time_available_weeks} weeks
{rag_section}
CURRENT SKILLS: {current_str}
MISSING SKILLS (highest priority): {missing_str}
EXISTING PROJECTS (don't repeat these): {existing_str}

INSTRUCTIONS:
1. Recommend exactly 3 projects ordered by impact (most impactful first).
2. Projects must close the highest-priority skill gaps.
3. Build on existing skills where possible — don't start from scratch.
4. Time estimates must fit within the {time_available_weeks}-week total budget.
5. Avoid recommending projects similar to existing ones.

Return ONLY the JSON object."""
