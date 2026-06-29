"""
app/agents/personal/spoken_english_agent.py
─────────────────────────────────────────────
Spoken English Agent — LangGraph node implementation.

Reads from state:
  spoken_text, english_context_type, question_answered
  target_role, resume_analysis (for personalised scripts)
  rag_context (injected by enrich_state_with_rag)

Writes to state:
  english_output
  agents_called — appends AgentName.SPOKEN_ENGLISH
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.personal.spoken_english_prompts import (
    ENGLISH_EVAL_SYSTEM,
    SCRIPT_GENERATION_SYSTEM,
    build_english_eval_prompt,
    build_script_generation_prompt,
)
from app.agents.state import AgentName, CareerCopilotState
from app.llm.gemini_client import get_gemini_flash
from app.rag.rag_pipeline import enrich_state_with_rag

logger = logging.getLogger(__name__)

# Minimum text length to evaluate (very short text gives no signal)
MIN_TEXT_LENGTH = 20


async def spoken_english_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    LangGraph node: Spoken English Agent.

    Two modes:
    1. EVALUATE — user provides spoken_text → full evaluation + corrected text
    2. SCRIPTS  — user provides no spoken_text → generate personalised practice scripts
    """
    logger.info(
        f"[EnglishAgent] Starting | user={state.get('user_id')} | "
        f"context={state.get('english_context_type')}"
    )

    spoken_text    = state.get("spoken_text", "").strip()
    context_type   = state.get("english_context_type", "interview_answer")
    question       = state.get("question_answered", "")
    target_role    = state.get("target_role", "Software Engineer")
    resume         = state.get("resume_analysis", {})
    resume_skills  = resume.get("extracted_skills", [])

    # ── Mode: Script generation (no input text provided) ──────────────────────
    if len(spoken_text) < MIN_TEXT_LENGTH:
        logger.info("[EnglishAgent] No spoken_text — generating practice scripts")
        return await _generate_scripts(state, target_role, resume_skills)

    # ── Guard: reject gibberish / non-language input ──────────────────────────
    # The LLM will otherwise fabricate a plausible-looking score for random
    # characters. Catch obvious nonsense deterministically (also saves a token call).
    if _looks_like_gibberish(spoken_text):
        logger.info("[EnglishAgent] Input looks like gibberish — returning low score without LLM call")
        return {
            "english_output": _gibberish_result(spoken_text),
            "agents_called": [AgentName.SPOKEN_ENGLISH],
        }

    # ── Mode: Full evaluation ─────────────────────────────────────────────────
    # RAG enrichment
    rag_update  = await enrich_state_with_rag(state, AgentName.SPOKEN_ENGLISH)
    rag_context = rag_update.get("rag_context", [])
    logger.info(f"[EnglishAgent] RAG retrieved {len(rag_context)} chunks")

    try:
        llm = get_gemini_flash()
        human_prompt = build_english_eval_prompt(
            spoken_text=spoken_text,
            context_type=context_type,
            question_answered=question,
            target_role=target_role,
            resume_skills=resume_skills,
            rag_context=rag_context,
        )

        response = await llm.ainvoke([
            SystemMessage(content=ENGLISH_EVAL_SYSTEM),
            HumanMessage(content=human_prompt),
        ])

        result = _parse_english_response(response.content)

        logger.info(
            f"[EnglishAgent] Evaluation done | "
            f"overall_score={result.get('scores', {}).get('overall')} | "
            f"issues={len(result.get('issues', []))} | "
            f"user={state.get('user_id')}"
        )

        return {
            "english_output": result,
            "agents_called": [AgentName.SPOKEN_ENGLISH],
        }

    except Exception as e:
        logger.error(f"[EnglishAgent] Evaluation failed: {e}", exc_info=True)
        return {
            "english_output": _fallback_output(str(e)),
            "error": str(e),
            "error_agent": AgentName.SPOKEN_ENGLISH,
            "agents_called": [AgentName.SPOKEN_ENGLISH],
        }


async def _generate_scripts(
    state: CareerCopilotState,
    target_role: str,
    resume_skills: list[str],
) -> dict[str, Any]:
    """Generate personalised practice scripts when no input text is given."""
    experience_level  = state.get("experience_level", "fresher")
    resume            = state.get("resume_analysis", {})
    strengths         = resume.get("strengths", [])

    try:
        llm = get_gemini_flash()
        human_prompt = build_script_generation_prompt(
            target_role=target_role,
            skills=resume_skills,
            experience_level=experience_level,
            notable_projects=strengths[:3],
        )

        response = await llm.ainvoke([
            SystemMessage(content=SCRIPT_GENERATION_SYSTEM),
            HumanMessage(content=human_prompt),
        ])

        raw     = response.content
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
        start   = cleaned.find("{")
        end     = cleaned.rfind("}") + 1
        scripts = json.loads(cleaned[start:end]) if start != -1 else {}

        result = {
            "corrected_text": "",
            "scores": {},
            "issues": [],
            "annotations": [],
            "star_compliance": {},
            "vocabulary_upgrades": [],
            "practice_scripts": scripts,
            "top_3_improvements": [],
            "encouragement": "Here are your personalised practice scripts. Use them to rehearse until they feel natural.",
        }

        logger.info(f"[EnglishAgent] Scripts generated | user={state.get('user_id')}")
        return {
            "english_output": result,
            "agents_called": [AgentName.SPOKEN_ENGLISH],
        }

    except Exception as e:
        logger.error(f"[EnglishAgent] Script generation failed: {e}", exc_info=True)
        return {
            "english_output": _fallback_output(str(e)),
            "error": str(e),
            "error_agent": AgentName.SPOKEN_ENGLISH,
            "agents_called": [AgentName.SPOKEN_ENGLISH],
        }


# ── Gibberish detection ─────────────────────────────────────────────────────
# Common English function words — virtually every genuine answer contains at
# least one. Their total absence is a strong signal the text isn't real English.
_COMMON_WORDS = {
    "i", "a", "an", "the", "to", "and", "is", "am", "are", "was", "were", "be",
    "of", "in", "it", "on", "as", "at", "by", "for", "with", "you", "me", "we",
    "my", "our", "your", "that", "this", "have", "has", "had", "but", "or", "so",
    "if", "not", "can", "will", "would", "should", "about", "do", "did", "from",
    "they", "them", "their", "what", "when", "which", "who", "how", "why", "then",
    "because", "while", "also", "more", "very", "into", "after", "before",
    "work", "experience", "project", "team", "skills", "developed", "built",
    "created", "using", "used", "data", "model", "learning", "role", "company",
    "good", "help", "want", "like", "make", "new", "years", "year",
}


def _word_is_suspicious(w: str) -> bool:
    """A single token looks non-linguistic (random keystrokes)."""
    if re.search(r"[bcdfghjklmnpqrstvwxyz]{4,}", w):  # 4+ consonants in a row
        return True
    vowels = sum(c in "aeiou" for c in w)
    ratio = vowels / max(len(w), 1)
    if ratio < 0.20:
        return True
    if len(w) >= 12 and ratio < 0.35:
        return True
    return False


def _looks_like_gibberish(text: str) -> bool:
    """
    Heuristic: flag obvious random-character input while avoiding false
    positives on real (even technical) answers. Triggers only when the text
    contains NO common English words AND most tokens look non-linguistic.
    """
    words = re.findall(r"[a-zA-Z]+", text.lower())
    if not words:
        return True
    if any(w in _COMMON_WORDS for w in words):
        return False  # has real function words → treat as genuine
    suspicious = sum(_word_is_suspicious(w) for w in words)
    if len(words) == 1:
        return _word_is_suspicious(words[0]) and len(words[0]) >= 8
    return suspicious / len(words) >= 0.5


def _gibberish_result(text: str) -> dict:
    """Low, honest score for input that isn't meaningful English."""
    return {
        "original_text": text,
        "corrected_text": "",
        "scores": {"grammar": 5, "fluency": 5, "structure": 5, "vocabulary": 5, "conciseness": 5, "overall": 5},
        "issues": [{
            "type": "clarity",
            "found": text[:60],
            "suggestion": "Enter a real answer in English.",
            "explanation": "This doesn't look like a meaningful English response, so it can't be scored properly. Type or speak a genuine answer to the question.",
        }],
        "annotations": [],
        "star_compliance": {
            "situation": False, "task": False, "action": False, "result": False,
            "score": 0, "missing": "A real answer is needed first.",
            "tip": "Answer the question in complete English sentences.",
        },
        "vocabulary_upgrades": [],
        "practice_scripts": {},
        "top_3_improvements": [
            "Provide a genuine, coherent answer in English.",
            "Use complete sentences that address the question.",
            "Aim for 4–8 sentences for an interview answer.",
        ],
        "encouragement": "That didn't look like a real answer — give it a proper try and I'll give you detailed, useful feedback.",
    }


def _parse_english_response(raw: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
    start   = cleaned.find("{")
    end     = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]
    try:
        return _validate_english_output(json.loads(cleaned))
    except json.JSONDecodeError as e:
        logger.error(f"[EnglishAgent] JSON parse error: {e}")
        return _fallback_output("Could not parse evaluation. Please try again.")


def _validate_english_output(data: dict) -> dict:
    data.setdefault("original_text", "")
    data.setdefault("corrected_text", "")
    data.setdefault("scores", {
        "grammar": 0, "fluency": 0, "structure": 0,
        "vocabulary": 0, "conciseness": 0, "overall": 0,
    })
    data.setdefault("issues", [])
    data.setdefault("annotations", [])
    data.setdefault("star_compliance", {
        "situation": False, "task": False, "action": False, "result": False,
        "score": 0, "missing": "", "tip": "",
    })
    data.setdefault("vocabulary_upgrades", [])
    data.setdefault("practice_scripts", {})
    data.setdefault("top_3_improvements", [])
    data.setdefault("encouragement", "")
    return data


def _fallback_output(error_message: str) -> dict:
    return {
        "original_text": "",
        "corrected_text": "",
        "scores": {"grammar": 0, "fluency": 0, "structure": 0, "vocabulary": 0, "conciseness": 0, "overall": 0},
        "issues": [],
        "annotations": [],
        "star_compliance": {"situation": False, "task": False, "action": False, "result": False, "score": 0, "missing": "", "tip": ""},
        "vocabulary_upgrades": [],
        "practice_scripts": {},
        "top_3_improvements": [],
        "encouragement": "",
        "error_reason": error_message,
    }
