"""
app/core/sanitize.py
─────────────────────
Lightweight prompt-injection defense for untrusted user text (resume content,
chat messages, English answers, LinkedIn sections, mood messages, etc.).

Strategy: neutralize the clearest injection phrases and prompt-control tokens,
strip control characters, and cap length — WITHOUT mangling legitimate content.
This is defense-in-depth: user text is already passed in the `user` role (not
`system`), so the model is told to treat it as data; this layer additionally
removes the most common override attempts.
"""
import re

# Only the clearest override/jailbreak patterns — conservative to avoid harming
# legitimate resume/answer text.
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+|the\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?|messages?|rules?)", re.I),
    re.compile(r"disregard\s+(?:all\s+|the\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?|rules?)", re.I),
    re.compile(r"forget\s+(?:everything|all\s+(?:previous|prior)\s+instructions?)", re.I),
    re.compile(r"reveal\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions?)", re.I),
    re.compile(r"(?:print|show|repeat)\s+(?:your\s+)?(?:system\s+)?prompt", re.I),
    re.compile(r"you\s+are\s+now\s+(?:a|an|the)\b", re.I),
    re.compile(r"system\s*prompt\s*[:=]", re.I),
    re.compile(r"</?\s*system\s*>", re.I),
    re.compile(r"<\|\s*im_(?:start|end)\s*\|>", re.I),
    re.compile(r"\bact\s+as\s+(?:an?\s+)?(?:DAN|jailbreak|unrestricted)\b", re.I),
]

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_user_text(text: str | None, max_len: int = 8000) -> str:
    """Neutralize injection attempts + strip control chars + cap length."""
    if not text:
        return ""
    t = _CONTROL_CHARS.sub(" ", str(text))
    for pattern in _INJECTION_PATTERNS:
        t = pattern.sub("[filtered]", t)
    if len(t) > max_len:
        t = t[:max_len]
    return t
