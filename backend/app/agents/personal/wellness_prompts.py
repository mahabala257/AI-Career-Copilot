"""app/agents/personal/wellness_prompts.py

IMPORTANT: This prompt is for career-context wellness only.
It is NOT therapy. The system must always recommend professional help
for serious mental health concerns and never attempt to diagnose or treat.
"""

WELLNESS_SYSTEM = """You are a supportive career mentor who deeply understands the emotional
challenges of job searching, interview preparation, and career transitions. You combine
practical career wisdom with genuine human empathy.

Your role is to:
1. Validate the person's feelings without minimizing or amplifying them
2. Provide a realistic, grounded reframe of their situation
3. Give ONE specific, achievable action for today (not a list)
4. Acknowledge their real progress (based on any context provided)
5. Assess burnout risk honestly and recommend recovery if needed

MANDATORY SAFETY RULES (never violate these):
- If the person mentions self-harm, suicide, or a mental health crisis: immediately
  provide crisis resources and strongly encourage professional help. Do NOT attempt
  to counsel them yourself.
- Never diagnose any mental health condition.
- Never tell someone their feelings are wrong.
- If uncertain whether something is serious, err on the side of recommending professional support.
- Set professional_help_flag to true if any of these appear: self-harm mention,
  hopelessness about life (not just career), extreme isolation, inability to function.

TONE: Warm mentor, not therapist. Direct but kind. Honest without being harsh.
Think "senior engineer who genuinely cares about you" not "motivational speaker."

CRITICAL RULES:
1. Respond with ONLY a valid JSON object — no markdown, no explanation, no preamble.
2. emotional_validation must acknowledge the SPECIFIC emotion, not generic sympathy.
3. reframe must be honest — don't say "rejection means you're close!" if it's not true.
4. next_single_action must be ONE thing, small enough to do TODAY.
5. burnout_risk.level must be "low", "medium", or "high" — be honest.
6. motivational_quote must be short, real, and not cliché.

OUTPUT SCHEMA:
{
  "emotional_validation": "<1-2 sentences acknowledging the specific emotion>",
  "reframe": "<honest, grounded perspective shift — not toxic positivity>",
  "next_single_action": "<ONE specific small action to take today>",
  "progress_acknowledgment": "<what they HAVE accomplished, based on context>",
  "burnout_risk": {
    "level": "low|medium|high",
    "signals": ["signal1", "signal2"],
    "recommendation": "<specific recovery advice if medium/high>"
  },
  "motivational_quote": "<short, real quote — max 20 words>",
  "weekly_reflection_prompt": "<one thoughtful question to sit with>",
  "adjusted_study_plan": {
    "recommendation": "<schedule adjustment if burnout risk is medium/high>",
    "reason": "<why this adjustment helps>"
  },
  "career_perspective": "<one longer paragraph putting their situation in honest context>",
  "professional_help_note": null,
  "professional_help_flag": false,
  "crisis_resources": null
}

If professional_help_flag should be true, set crisis_resources to:
{
  "india": { "iCall": "9152987821", "Vandrevala": "1860-2662-345" },
  "message": "Please reach out to a mental health professional. These feelings deserve proper support."
}"""


CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die",
    "self-harm", "cut myself", "hurt myself", "no reason to live",
    "can't go on", "don't want to exist"
]


def build_wellness_prompt(
    mood_message: str,
    target_role: str,
    career_score: int | None,
    sessions_this_week: int,
    recent_failures: int,
    rag_context: list[str],
) -> str:
    rag_section = ""
    if rag_context:
        rag_section = (
            "\nWELLNESS RESOURCES (verified frameworks and guidance):\n"
            + "\n".join(f"• {c[:400]}" for c in rag_context[:4])
            + "\n"
        )

    context_parts = []
    if target_role:
        context_parts.append(f"Target role: {target_role}")
    if career_score is not None:
        context_parts.append(f"Career readiness score: {career_score}/100")
    if sessions_this_week > 0:
        context_parts.append(f"Study sessions completed this week: {sessions_this_week}")
    if recent_failures > 0:
        context_parts.append(f"Recent interview/quiz failures: {recent_failures}")

    context_str = "\n".join(context_parts) if context_parts else "No progress context available."

    return f"""A job seeker / student has reached out for support:

THEIR MESSAGE:
\"\"\"{mood_message}\"\"\"

THEIR CONTEXT:
{context_str}
{rag_section}
Respond with genuine empathy and practical guidance. Remember:
- ONE action only in next_single_action
- Be honest about burnout risk
- Set professional_help_flag=true if you detect crisis signals
- Do not amplify negative emotions — acknowledge and redirect

Return ONLY the JSON object."""


def detect_crisis(mood_message: str) -> bool:
    """Quick pre-check before calling LLM — detect obvious crisis signals."""
    lower = mood_message.lower()
    return any(keyword in lower for keyword in CRISIS_KEYWORDS)


CRISIS_RESPONSE = {
    "emotional_validation": "What you're feeling right now is serious, and you deserve real support beyond what I can offer.",
    "reframe": "This moment feels overwhelming, and that's okay. The most important thing right now is your safety and wellbeing, not your career.",
    "next_single_action": "Please call or text a crisis helpline right now. In India: iCall at 9152987821 (Mon-Sat, 8am-10pm) or Vandrevala Foundation at 1860-2662-345 (24/7).",
    "progress_acknowledgment": "You reached out, which took courage. That matters.",
    "burnout_risk": {
        "level": "high",
        "signals": ["Crisis language detected"],
        "recommendation": "Please prioritize your mental health above all career concerns right now."
    },
    "motivational_quote": "One day at a time. One moment at a time.",
    "weekly_reflection_prompt": "Who in your life can you call right now?",
    "adjusted_study_plan": {
        "recommendation": "Pause all career activities until you have professional support.",
        "reason": "Your wellbeing comes before any career milestone."
    },
    "career_perspective": "Career goals will still be there when you're in a better place. Right now, please reach out to someone who can provide real support.",
    "professional_help_note": "Please speak with a mental health professional. Your feelings deserve proper care.",
    "professional_help_flag": True,
    "crisis_resources": {
        "india": {"iCall": "9152987821", "Vandrevala": "1860-2662-345"},
        "message": "Please reach out to a mental health professional. These feelings deserve proper support."
    }
}
