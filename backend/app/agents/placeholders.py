"""
app/agents/placeholders.py
───────────────────────────
Placeholder (stub) nodes for all 5 Phase 1 specialized agents.

Why stubs instead of leaving them empty?
  - The graph can be compiled and tested RIGHT NOW without real LLM logic
  - Each stub returns correctly structured state updates — so the synthesizer,
    router, and LangFuse tracing all work end-to-end today
  - When you implement each real agent (next steps), you replace ONLY that
    agent's module. The graph wiring, router, and state schema don't change.
  - Makes integration testing possible: you can test the full graph flow
    with predictable stub outputs before the real agents are ready

Each stub:
  1. Logs that it was called
  2. Records itself in agents_called
  3. Returns a realistically shaped (but hardcoded) output dict
  4. Uses the exact same state keys the real agent will use

Replace each stub by implementing the real agent in its dedicated module
(app/agents/career/resume_agent.py, etc.) and updating the import in graph.py.
"""

import logging
from typing import Any

from app.agents.state import AgentName, CareerCopilotState

logger = logging.getLogger(__name__)


# ── Resume Agent Stub ──────────────────────────────────────────────────────────
async def resume_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    Stub for Resume Agent.
    Real implementation: app/agents/career/resume_agent.py
    
    Will: parse PDF, extract skills, score ATS, generate suggestions via Gemini + RAG
    """
    logger.info(f"[ResumeAgent-STUB] Called for user {state.get('user_id')}")

    resume_text = state.get("resume_text", "")
    target_role = state.get("target_role", "Software Engineer")

    # Return a realistic stub output so the synthesizer and frontend can be
    # developed and tested before the real agent is implemented
    return {
        "resume_analysis": {
            "ats_score": 72,
            "extracted_skills": ["Python", "SQL", "Machine Learning", "NumPy", "Pandas"],
            "missing_skills": ["Docker", "Kubernetes", "AWS", "MLOps", "FastAPI"],
            "strengths": [
                "Strong Python foundation",
                "Good data analysis skills",
                "Academic ML projects",
            ],
            "suggestions": [
                "Add quantified project impact metrics (e.g., 'improved accuracy by 15%')",
                "Include a professional summary at the top",
                "Add GitHub links to projects",
                "List certifications if available",
            ],
            "target_role_match": target_role,
            "analysis_note": "[STUB] Real analysis will use Gemini + ChromaDB RAG",
        },
        "agents_called": [AgentName.RESUME],
    }


# ── Skill Gap Agent Stub ───────────────────────────────────────────────────────
async def skill_gap_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    Stub for Skill Gap Agent.
    Real implementation: app/agents/career/skill_gap_agent.py
    
    Will: compare user skills vs target role requirements via Gemini + RAG on job specs
    """
    logger.info(f"[SkillGapAgent-STUB] Called for user {state.get('user_id')}")

    target_role = state.get("target_role", "AI Engineer")

    # Pull current skills from state (could come from resume_analysis or user profile)
    resume_analysis = state.get("resume_analysis", {})
    current_skills = resume_analysis.get("extracted_skills", ["Python", "SQL"])

    return {
        "skill_gap_analysis": {
            "target_role": target_role,
            "current_skills": current_skills,
            "required_skills": [
                "Python", "SQL", "Machine Learning", "Deep Learning",
                "Docker", "Kubernetes", "AWS", "FastAPI", "LangChain",
                "LangGraph", "ChromaDB", "MLOps",
            ],
            "missing_skills": ["Docker", "Kubernetes", "AWS", "LangChain", "LangGraph", "MLOps"],
            "priority_order": [
                "Docker",        # High demand, 2 weeks to learn
                "AWS basics",    # High demand, 4 weeks
                "LangChain",     # AI-specific, 2 weeks
                "MLOps",         # Career differentiator, 6 weeks
                "Kubernetes",    # Advanced, 4 weeks
            ],
            "time_estimates": {
                "Docker": "2 weeks",
                "AWS basics": "4 weeks",
                "LangChain": "2 weeks",
                "MLOps": "6 weeks",
                "Kubernetes": "4 weeks",
            },
            "analysis_note": "[STUB] Real analysis will use Gemini + ChromaDB job spec RAG",
        },
        "agents_called": [AgentName.SKILL_GAP],
    }


# ── Interview Agent Stub ───────────────────────────────────────────────────────
async def interview_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    Stub for Interview Agent.
    Real implementation: app/agents/interview/interview_agent.py
    
    Will: generate questions using Groq (fast) + ChromaDB interview Q's collection
    """
    logger.info(f"[InterviewAgent-STUB] Called for user {state.get('user_id')}")

    interview_type = state.get("interview_type", "technical")
    target_role = state.get("target_role", "AI Engineer")

    stub_questions = {
        "technical": [
            {
                "question": "Explain the difference between RAG and fine-tuning. When would you use each?",
                "expected_answer": "RAG retrieves external knowledge at inference time; fine-tuning updates model weights on domain-specific data. Use RAG for dynamic/frequently updated knowledge, fine-tuning for consistent style/behavior.",
                "difficulty": "medium",
            },
            {
                "question": "What is the vanishing gradient problem in deep neural networks?",
                "expected_answer": "Gradients shrink exponentially during backpropagation through many layers, making early layers learn very slowly. Solved by ReLU activations, batch normalization, residual connections.",
                "difficulty": "medium",
            },
            {
                "question": "Describe the architecture of a Transformer model.",
                "expected_answer": "Encoder-decoder architecture with multi-head self-attention, positional encoding, feed-forward layers, and layer normalization. Attention mechanism weighs relationships between all token pairs.",
                "difficulty": "hard",
            },
        ],
        "hr": [
            {
                "question": "Tell me about yourself.",
                "expected_answer": "Structure: present role/background → relevant skills → why this company/role → future goals.",
                "difficulty": "easy",
            },
            {
                "question": "Where do you see yourself in 5 years?",
                "expected_answer": "Align with company growth, show ambition balanced with realism, tie to the role you're interviewing for.",
                "difficulty": "easy",
            },
        ],
        "coding": [
            {
                "question": "Implement a function to find the two numbers in an array that add up to a target sum.",
                "expected_answer": "Use a hash map: for each number, check if (target - number) is in the map. O(n) time complexity.",
                "difficulty": "easy",
            },
        ],
    }

    questions = stub_questions.get(interview_type, stub_questions["technical"])

    return {
        "interview_output": {
            "session_type": interview_type,
            "target_role": target_role,
            "questions": questions,
            "total_questions": len(questions),
            "estimated_duration_minutes": len(questions) * 5,
            "analysis_note": "[STUB] Real questions will be generated by Groq + ChromaDB RAG",
        },
        "agents_called": [AgentName.INTERVIEW],
    }


# ── Quiz Agent Stub ────────────────────────────────────────────────────────────
async def quiz_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    Stub for Quiz & Assessment Agent.
    Real implementation: app/agents/interview/quiz_agent.py
    
    Will: generate MCQs using Groq, evaluate submitted answers, identify weak areas
    """
    logger.info(f"[QuizAgent-STUB] Called for user {state.get('user_id')}")

    topic = state.get("quiz_topic", "Machine Learning")
    difficulty = state.get("quiz_difficulty", "medium")

    return {
        "quiz_output": {
            "topic": topic,
            "difficulty": difficulty,
            "questions": [
                {
                    "id": 1,
                    "question": "What is the purpose of the bias term in a neural network?",
                    "options": [
                        "A. To scale the weights",
                        "B. To shift the activation function",
                        "C. To reduce overfitting",
                        "D. To normalize inputs",
                    ],
                    "correct_answer": "B",
                    "explanation": "The bias term shifts the activation function, allowing the model to fit data that doesn't pass through the origin.",
                },
                {
                    "id": 2,
                    "question": "Which algorithm is used in the backpropagation process?",
                    "options": [
                        "A. Gradient Descent",
                        "B. Random Forest",
                        "C. K-Means",
                        "D. PCA",
                    ],
                    "correct_answer": "A",
                    "explanation": "Backpropagation uses gradient descent (or its variants like Adam, SGD) to minimize the loss function by updating weights.",
                },
                {
                    "id": 3,
                    "question": "What does 'overfitting' mean in machine learning?",
                    "options": [
                        "A. The model performs well on training data but poorly on new data",
                        "B. The model is too simple to learn patterns",
                        "C. The model trains too slowly",
                        "D. The model uses too little data",
                    ],
                    "correct_answer": "A",
                    "explanation": "Overfitting occurs when a model memorizes training data, including noise, causing poor generalization.",
                },
            ],
            "total_questions": 3,
            "weak_areas": [],    # Populated after user submits answers
            "analysis_note": "[STUB] Real MCQs will be generated by Groq + ChromaDB",
        },
        "agents_called": [AgentName.QUIZ],
    }


# ── Study Planner Agent Stub ───────────────────────────────────────────────────
async def study_planner_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    Stub for Study Planner Agent.
    Real implementation: app/agents/personal/study_planner_agent.py
    
    Will: generate structured daily/weekly/monthly plans using Groq,
    based on skill gaps and user's available hours
    """
    logger.info(f"[StudyPlannerAgent-STUB] Called for user {state.get('user_id')}")

    plan_type = state.get("plan_type", "weekly")
    available_hours = state.get("available_hours", 2.0)
    target_role = state.get("target_role", "AI Engineer")

    # Pull skill gaps if available from previous agent
    skill_gap = state.get("skill_gap_analysis", {})
    priority_skills = skill_gap.get("priority_order", ["Python", "Docker", "LangChain"])

    weekly_plan = {
        "plan_type": plan_type,
        "target_role": target_role,
        "available_hours_per_day": available_hours,
        "days": [
            {
                "day": "Monday",
                "focus": priority_skills[0] if priority_skills else "Python",
                "tasks": [
                    f"Watch 2 tutorial videos on {priority_skills[0] if priority_skills else 'Python'}",
                    "Complete 3 practice exercises",
                    "Read official documentation for 30 minutes",
                ],
                "estimated_hours": available_hours,
            },
            {
                "day": "Tuesday",
                "focus": priority_skills[0] if priority_skills else "Python",
                "tasks": [
                    "Build a small hands-on project",
                    "Review yesterday's concepts",
                    "Take a mini quiz",
                ],
                "estimated_hours": available_hours,
            },
            {
                "day": "Wednesday",
                "focus": priority_skills[1] if len(priority_skills) > 1 else "SQL",
                "tasks": [
                    f"Start {priority_skills[1] if len(priority_skills) > 1 else 'SQL'} basics",
                    "Complete beginner exercises",
                    "Watch 1 overview video",
                ],
                "estimated_hours": available_hours,
            },
            {
                "day": "Thursday",
                "focus": "Interview Prep",
                "tasks": [
                    "Practice 5 technical interview questions",
                    "Review data structures and algorithms",
                    "Mock HR interview session",
                ],
                "estimated_hours": available_hours,
            },
            {
                "day": "Friday",
                "focus": "Project Work",
                "tasks": [
                    "Work on portfolio project",
                    "Push code to GitHub",
                    "Write a brief project README",
                ],
                "estimated_hours": available_hours,
            },
            {
                "day": "Saturday",
                "focus": "Review & Quiz",
                "tasks": [
                    "Review the week's learning",
                    "Take a full quiz on covered topics",
                    "Update LinkedIn with new skills",
                ],
                "estimated_hours": available_hours * 1.5,
            },
            {
                "day": "Sunday",
                "focus": "Rest / Light Review",
                "tasks": [
                    "Read one article on AI trends",
                    "Plan next week's focus areas",
                ],
                "estimated_hours": 0.5,
            },
        ],
        "weekly_goal": f"Master fundamentals of {priority_skills[0] if priority_skills else 'core skills'}",
        "analysis_note": "[STUB] Real plan will be generated by Groq based on skill gaps",
    }

    return {
        "study_plan_output": weekly_plan,
        "agents_called": [AgentName.STUDY_PLANNER],
    }
