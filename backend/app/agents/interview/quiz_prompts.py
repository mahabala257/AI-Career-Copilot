"""
app/agents/interview/quiz_prompts.py
──────────────────────────────────────
All prompt templates for the Quiz & Assessment Agent.

Quiz types covered
───────────────────
  1. MCQ Quiz      — 4-option multiple choice, auto-scorable
  2. Coding Quiz   — short coding problems (write a function)
  3. Mixed Quiz    — blend of MCQ + short answer

Weak area detection design
────────────────────────────
After the user submits answers, a second Gemini call analyses which questions
were answered incorrectly and groups them into "weak areas" (topic clusters).
This is more useful than just saying "you got 6/10" — it tells the user
"you're weak in Backpropagation and Regularisation" which feeds into:
  - Study Planner Agent (adds weak topics to the plan)
  - Interview Agent (generates extra questions on weak areas next time)
  - Dashboard (shows weak area radar chart)

Difficulty calibration
───────────────────────
  easy   → fresher level, tests basic definitions and recall
  medium → mid-level, tests application and understanding
  hard   → senior level, tests edge cases and deep understanding
"""

# ── MCQ Generation Prompt ─────────────────────────────────────────────────────

MCQ_SYSTEM = """You are an expert technical assessment designer who creates high-quality
multiple choice questions for software engineering and AI/ML certification exams.

Generate challenging, unambiguous MCQ questions that genuinely test understanding,
not just memorisation. Each question should have exactly 4 options where only
one is clearly correct.

CRITICAL: Respond with ONLY a valid JSON object. No markdown, no preamble.

OUTPUT SCHEMA:
{
  "quiz_type": "mcq",
  "topic": "<topic name>",
  "difficulty": "<easy|medium|hard>",
  "questions": [
    {
      "id": 1,
      "question": "What does the 'learning rate' hyperparameter control in gradient descent?",
      "options": {
        "A": "The number of training epochs",
        "B": "The step size when updating model weights",
        "C": "The size of each training batch",
        "D": "The threshold for early stopping"
      },
      "correct_answer": "B",
      "explanation": "The learning rate controls how large each weight update step is. Too high causes overshooting; too low causes slow convergence.",
      "topic_area": "Optimisation",
      "difficulty": "easy",
      "why_this_matters": "Understanding learning rate is fundamental to training any neural network"
    }
  ],
  "topic_areas_covered": ["Optimisation", "Neural Networks"],
  "total_questions": 10
}"""


def build_mcq_prompt(topic: str, difficulty: str, count: int) -> str:
    difficulty_guide = {
        "easy":   "Test basic definitions, terminology, and simple concepts. Questions should be answerable by a student who has read an intro tutorial.",
        "medium": "Test applied understanding. Questions should require knowing HOW things work, not just WHAT they are called.",
        "hard":   "Test deep knowledge, edge cases, and nuanced distinctions. Questions should challenge even experienced practitioners.",
    }.get(difficulty, "Test applied understanding.")

    return f"""Generate {count} MCQ questions on the topic: {topic}

Difficulty: {difficulty_guide}

Requirements:
- Each question must have exactly 4 options (A, B, C, D)
- Only one option should be clearly correct
- Distractors should be plausible (not obviously wrong)
- Cover different sub-topics within {topic}
- Include a clear explanation for the correct answer
- Questions should reflect what is commonly tested in {topic} job interviews

Return ONLY the JSON object."""


# ── Coding Quiz Prompt ─────────────────────────────────────────────────────────

CODING_QUIZ_SYSTEM = """You are a technical interviewer creating short coding assessment problems.
Generate concise coding problems that can be solved in 10-15 minutes.

CRITICAL: Respond with ONLY a valid JSON object. No markdown, no preamble.

OUTPUT SCHEMA:
{
  "quiz_type": "coding",
  "topic": "<topic name>",
  "difficulty": "<easy|medium|hard>",
  "questions": [
    {
      "id": 1,
      "question": "Write a Python function that reverses a string without using slicing.",
      "function_signature": "def reverse_string(s: str) -> str:",
      "examples": [
        {"input": "reverse_string('hello')", "output": "'olleh'"}
      ],
      "test_cases": [
        {"input": "hello",   "expected": "olleh"},
        {"input": "racecar", "expected": "racecar"},
        {"input": "",        "expected": ""}
      ],
      "hints": ["Think about iterating backwards"],
      "solution": "def reverse_string(s):\\n    result = ''\\n    for char in s:\\n        result = char + result\\n    return result",
      "solution_explanation": "Build the result by prepending each character",
      "topic_area": "Strings",
      "difficulty": "easy",
      "time_limit_minutes": 10
    }
  ],
  "total_questions": 5
}"""


def build_coding_quiz_prompt(topic: str, difficulty: str, count: int) -> str:
    return f"""Generate {count} short coding problems on: {topic}

Difficulty: {difficulty}

Requirements:
- Problems solvable in 10-15 minutes
- Provide complete Python solutions
- Include test cases for auto-grading
- Focus on practical, commonly-asked patterns for {topic}

Return ONLY the JSON object."""


# ── Score & Weak Area Detection Prompt ────────────────────────────────────────

SCORING_SYSTEM = """You are a quiz evaluator and learning advisor.
Analyse quiz results, calculate scores, identify weak areas, and provide 
personalised improvement recommendations.

CRITICAL: Respond with ONLY a valid JSON object. No markdown, no preamble.

OUTPUT SCHEMA:
{
  "total_questions": 10,
  "correct_answers": 7,
  "score_percent": 70,
  "grade": "good",
  "question_results": [
    {
      "question_id": 1,
      "user_answer": "B",
      "correct_answer": "A",
      "is_correct": false,
      "topic_area": "Optimisation",
      "explanation": "The correct answer is A because..."
    }
  ],
  "weak_areas": ["Backpropagation", "Regularisation"],
  "strong_areas": ["Activation Functions", "Loss Functions"],
  "topic_performance": {
    "Optimisation": {"correct": 1, "total": 3, "percent": 33},
    "Neural Networks": {"correct": 3, "total": 3, "percent": 100}
  },
  "improvement_recommendations": [
    "Review backpropagation chain rule — you got 0/2 questions on this",
    "Practice L1 vs L2 regularisation differences"
  ],
  "next_quiz_focus": ["Backpropagation", "Regularisation"],
  "encouragement": "You scored 70% — strong on architecture, focus on training optimisation next"
}"""


def build_scoring_prompt(
    questions: list[dict],
    user_answers: list[dict],
) -> str:
    """
    Build the scoring prompt by pairing each question with the user's answer.
    user_answers: [{"question_id": 1, "answer": "B"}, ...]
    """
    # Build answer lookup
    answer_map = {a.get("question_id", a.get("id")): a.get("answer", "") for a in user_answers}

    pairs = []
    for q in questions:
        qid    = q.get("id", 0)
        user_a = answer_map.get(qid, "Not answered")
        correct = q.get("correct_answer", "")
        pairs.append(
            f"Q{qid}: {q.get('question', '')[:120]}\n"
            f"  Options: {q.get('options', {})}\n"
            f"  Correct: {correct} | User answered: {user_a}\n"
            f"  Topic: {q.get('topic_area', 'General')}"
        )

    qa_text = "\n\n".join(pairs)
    return f"""Evaluate these quiz answers and identify weak areas:

{qa_text}

Calculate the score, identify weak topic areas, and give specific improvement advice.
Return ONLY the JSON object."""
