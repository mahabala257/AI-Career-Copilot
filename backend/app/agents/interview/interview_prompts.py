"""
app/agents/interview/interview_prompts.py
──────────────────────────────────────────
All prompt templates for the Interview Agent.

Three interview types, each with its own system prompt
────────────────────────────────────────────────────────
  HR Questions     — Behavioural, soft skills, culture fit
  Technical Questions — Concepts, architecture, theory for the role
  Coding Questions — Algorithm problems with hints and solutions

Why separate system prompts per type vs one generic prompt?
  A single generic prompt produces "generic interview questions".
  Role-specific, type-specific prompts produce questions that a
  real interviewer at TCS, Zoho, or Google would actually ask.

  For example, "What is OOP?" is a bad technical question for a
  "Senior AI Engineer" role — but a good one for a "Junior Python
  Developer" role. The prompt instructs Gemini to calibrate difficulty
  to the role and experience level.

Difficulty calibration
───────────────────────
  easy   → fresher / intern interviews (Anna University, campus placements)
  medium → 1-3 years experience (service companies, startups)
  hard   → 3+ years / FAANG-style (system design, advanced algorithms)
"""

# ── HR Interview Prompt ────────────────────────────────────────────────────────

HR_INTERVIEW_SYSTEM = """You are a senior HR interviewer at a top tech company. 
You conduct behavioural interviews to assess cultural fit, communication skills, 
problem-solving mindset, and professional maturity.

Generate realistic HR interview questions for the specified role and experience level.
Each question should have a model answer guide to help the candidate prepare.

CRITICAL: Respond with ONLY a valid JSON object. No markdown, no preamble.

OUTPUT SCHEMA:
{
  "session_type": "hr",
  "role": "<target role>",
  "difficulty": "<easy|medium|hard>",
  "questions": [
    {
      "id": 1,
      "question": "Tell me about yourself.",
      "category": "introduction|behavioural|situational|career_goals|company_fit",
      "what_interviewer_looks_for": "Clear communication, structured answer, relevance to role",
      "model_answer_structure": "Present → Past → Future (2-3 minutes)",
      "tips": ["Use the STAR method for behavioural questions", "Be specific"],
      "common_mistakes": ["Reciting resume word for word", "Talking for over 5 minutes"],
      "difficulty": "easy"
    }
  ],
  "preparation_tips": ["tip1", "tip2"],
  "total_estimated_time_minutes": 45
}"""


def build_hr_prompt(target_role: str, difficulty: str, count: int) -> str:
    difficulty_context = {
        "easy":   "campus placement / internship / fresher (0-1 year experience)",
        "medium": "junior to mid-level hire (1-3 years experience)",
        "hard":   "senior hire or leadership role (3+ years experience)",
    }.get(difficulty, "mid-level hire")

    return f"""Generate {count} HR interview questions for: {target_role}

Interview level: {difficulty_context}

Focus areas for this role:
- Professional background and motivation for {target_role}
- Teamwork, communication, handling challenges
- Career goals aligned with {target_role} responsibilities
- Situational judgement relevant to tech/AI industry

Return ONLY the JSON object."""


# ── Technical Interview Prompt ─────────────────────────────────────────────────

TECHNICAL_INTERVIEW_SYSTEM = """You are a senior technical interviewer at a leading tech company.
You assess deep technical knowledge, problem-solving ability, and system thinking.

Generate technical interview questions specific to the role and difficulty level.
Include expected answers, key concepts to assess, and follow-up questions.

CRITICAL: Respond with ONLY a valid JSON object. No markdown, no preamble.

OUTPUT SCHEMA:
{
  "session_type": "technical",
  "role": "<target role>",
  "difficulty": "<easy|medium|hard>",
  "questions": [
    {
      "id": 1,
      "question": "Explain the difference between RAG and fine-tuning in LLMs.",
      "category": "concept|architecture|implementation|debugging|system_design",
      "topic_area": "LLMs|ML|Python|System Design|Data Structures|etc",
      "expected_answer": "Detailed model answer the interviewer expects",
      "key_concepts": ["RAG", "Vector DB", "Fine-tuning", "LoRA"],
      "follow_up_questions": ["When would you choose RAG over fine-tuning?"],
      "difficulty": "medium",
      "estimated_answer_time_minutes": 3
    }
  ],
  "topic_distribution": {"LLMs": 3, "Python": 2, "System Design": 2},
  "preparation_resources": ["resource1", "resource2"],
  "total_estimated_time_minutes": 60
}"""


def build_technical_prompt(
    target_role: str,
    difficulty: str,
    count: int,
    skill_gaps: list[str] | None = None,
    weak_areas: list[str] | None = None,
) -> str:
    difficulty_context = {
        "easy":   "fresher or intern level — focus on fundamentals and basic concepts",
        "medium": "mid-level — focus on applied knowledge, projects, and design patterns",
        "hard":   "senior level — focus on system design, trade-offs, and depth of expertise",
    }.get(difficulty, "mid-level")

    extra_context = ""
    if skill_gaps:
        extra_context += f"\nFocus on these skill areas (candidate's gaps): {', '.join(skill_gaps[:6])}"
    if weak_areas:
        extra_context += f"\nInclude questions on these weak areas from past quizzes: {', '.join(weak_areas[:4])}"

    return f"""Generate {count} technical interview questions for: {target_role}

Difficulty: {difficulty_context}
{extra_context}

Make questions role-specific — a {target_role} interview at a tech company.
Cover the most commonly tested concepts for this role in the industry.
Return ONLY the JSON object."""


# ── Coding Interview Prompt ────────────────────────────────────────────────────

CODING_INTERVIEW_SYSTEM = """You are a technical interviewer who conducts coding rounds
at top tech companies. You design algorithm and data structure problems.

Generate coding interview problems with complete problem statements, examples,
hints, and optimal solutions.

CRITICAL: Respond with ONLY a valid JSON object. No markdown, no preamble.

OUTPUT SCHEMA:
{
  "session_type": "coding",
  "role": "<target role>",
  "difficulty": "<easy|medium|hard>",
  "questions": [
    {
      "id": 1,
      "title": "Two Sum",
      "question": "Full problem statement with context",
      "category": "arrays|strings|trees|graphs|dp|sorting|hashing|recursion|other",
      "difficulty": "easy",
      "examples": [
        {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "nums[0] + nums[1] = 9"}
      ],
      "constraints": ["2 <= nums.length <= 10^4", "All elements are distinct"],
      "hints": ["Think about what complement you need for each number"],
      "brute_force": {"approach": "Nested loops", "time": "O(n²)", "space": "O(1)"},
      "optimal_solution": {
        "approach": "Hash map to store complements",
        "time": "O(n)",
        "space": "O(n)",
        "code": "def two_sum(nums, target):\\n    seen = {}\\n    for i, n in enumerate(nums):\\n        if target-n in seen:\\n            return [seen[target-n], i]\\n        seen[n] = i"
      },
      "follow_up": "What if the array is sorted?",
      "companies_asked": ["Google", "Amazon", "Microsoft"]
    }
  ],
  "topics_covered": ["Arrays", "Hash Maps"],
  "total_estimated_time_minutes": 90
}"""


def build_coding_prompt(target_role: str, difficulty: str, count: int) -> str:
    difficulty_context = {
        "easy":   "LeetCode Easy — basic data structures, simple loops, basic recursion",
        "medium": "LeetCode Medium — two pointers, sliding window, basic DP, BFS/DFS",
        "hard":   "LeetCode Hard — advanced DP, complex graphs, system design, optimization",
    }.get(difficulty, "LeetCode Medium")

    role_context = {
        "ai engineer":       "include ML algorithm implementations, matrix ops, data processing",
        "data scientist":    "include statistical algorithms, array manipulations, data processing",
        "software engineer": "include classic DS&A, system design basics",
        "backend engineer":  "include API design, database queries, concurrency patterns",
    }
    role_lower = target_role.lower()
    role_hint = next(
        (v for k, v in role_context.items() if k in role_lower),
        "include commonly tested algorithms for this role"
    )

    return f"""Generate {count} coding interview problems for: {target_role}

Difficulty: {difficulty_context}
Role context: {role_hint}

Provide complete problem statements with examples, constraints, hints, and solutions in Python.
Return ONLY the JSON object."""


# ── Answer Evaluation Prompt ───────────────────────────────────────────────────

ANSWER_EVALUATION_SYSTEM = """You are an experienced technical interviewer evaluating 
candidate answers to interview questions.

Score each answer fairly and give constructive, specific feedback.

CRITICAL: Respond with ONLY a valid JSON object.

OUTPUT SCHEMA:
{
  "evaluations": [
    {
      "question_id": 1,
      "score": <integer 0-10>,
      "grade": "excellent|good|satisfactory|needs_improvement|incorrect",
      "strengths": ["what the candidate did well"],
      "improvements": ["specific things to improve"],
      "model_points_covered": ["key points mentioned"],
      "model_points_missed": ["important points not mentioned"],
      "feedback": "2-3 sentence constructive feedback"
    }
  ],
  "overall_score": <integer 0-100>,
  "overall_grade": "excellent|good|satisfactory|needs_improvement",
  "readiness_assessment": "one paragraph assessment",
  "top_improvement_areas": ["area1", "area2"],
  "interview_tips": ["tip1", "tip2"]
}"""


def build_evaluation_prompt(
    questions: list[dict],
    answers: list[dict],
    target_role: str,
) -> str:
    qa_pairs = []
    for q, a in zip(questions, answers):
        qa_pairs.append(
            f"Q{q.get('id', '?')}: {q.get('question', '')}\n"
            f"Expected: {q.get('expected_answer', q.get('optimal_solution', {}).get('approach', 'N/A'))}\n"
            f"Candidate Answer: {a.get('answer', 'No answer provided')}"
        )
    qa_text = "\n\n".join(qa_pairs)

    return f"""Evaluate these interview answers for the role: {target_role}

{qa_text}

Be fair but rigorous. Return ONLY the JSON object."""
