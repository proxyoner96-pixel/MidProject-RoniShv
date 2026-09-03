"""
nlu.py
======
Natural Language Understanding layer.

Takes the user's free-text opening message ("קוראים לי רותם ויש לי תור
בתאריך 18.01.2027") and turns it into structured data:

    {"name": "רותם", "claimed_date": "2027-01-18"}

This is extraction, not RAG: Gemini is given a hard-constrained prompt and
forced to return ONLY JSON (via response_mime_type="application/json"), so
the caller can parse it reliably without regex gymnastics.

If Gemini is not configured or the call fails for any reason, this module
degrades gracefully to a small rule-based fallback so the rest of the app
(and local development without an API key yet) keeps working.
"""

import json
import re
from datetime import datetime

from gemini_client import generate, is_configured, GeminiNotConfigured

EXTRACTION_PROMPT = """You are the NLU layer of a Hebrew appointment-verification chatbot.
Extract structured data from the user's free-text message.

Return ONLY a JSON object with exactly these two keys:
  "name": the person's first name (or full name if given), as a string, or null if no name is mentioned.
  "claimed_date": a date the user mentions they believe their appointment is on,
                   formatted strictly as "YYYY-MM-DD", or null if no date is mentioned.

Rules:
- The message will usually be in Hebrew, but may mix in English or numerals.
- Dates may appear as DD.MM.YYYY, DD/MM/YYYY, or written out in Hebrew (e.g. "18 בינואר 2027").
  Always normalize to YYYY-MM-DD.
- If the year is missing, infer the closest plausible future year is NOT your job —
  just return null for claimed_date if the year is missing or ambiguous.
- Do not invent a name or date that is not actually present in the text.
- Do not include any explanation, markdown, or text outside the JSON object.

User message:
{message}
"""

# Very small fallback used only when Gemini is unavailable (e.g. no API key
# yet, during early local development). It's intentionally conservative:
# it only picks up an explicit numeric date, and treats the rest of the
# message as containing the name.
_DATE_PATTERNS = [
    (re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b"), "%d.%m.%Y"),
]


def _fallback_extract(message: str) -> dict:
    claimed_date = None
    for pattern, _fmt in _DATE_PATTERNS:
        m = pattern.search(message)
        if m:
            day, month, year = m.groups()
            try:
                dt = datetime(int(year), int(month), int(day))
                claimed_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                claimed_date = None
            break

    # Naive name guess: look for "קוראים לי <name...>" / "שמי <name...>".
    # Collects consecutive words after the trigger phrase (so "דני כהן" isn't
    # truncated to "דני"), but stops at the first connector word or any token
    # containing a digit, so it doesn't swallow "ויש לי תור ב-05/01/2026".
    name = None
    name_match = re.search(r"(?:קוראים לי|שמי)\s+(.+)", message)
    if name_match:
        stopwords = {"ו", "יש", "ולי", "לי", "שיש", "עם", "בתאריך", "ב", "תור"}
        collected = []
        for word in name_match.group(1).split():
            clean = word.strip(",.")
            if not clean or clean in stopwords or any(ch.isdigit() for ch in clean):
                break
            collected.append(clean)
            if len(collected) >= 3:
                break
        if collected:
            name = " ".join(collected)

    return {"name": name, "claimed_date": claimed_date}


def extract_name_and_date(message: str) -> dict:
    """
    Extract {"name": str|None, "claimed_date": "YYYY-MM-DD"|None} from free text.

    Never raises: on any Gemini/parsing failure, falls back to a best-effort
    rule-based extraction so the conversation can still proceed (or the bot
    can ask the user to rephrase).
    """
    if not is_configured():
        return _fallback_extract(message)

    try:
        raw = generate(EXTRACTION_PROMPT.format(message=message), json_mode=True)
        data = json.loads(raw)
        name = data.get("name")
        claimed_date = data.get("claimed_date")

        # Defensive validation — never trust the model blindly.
        if name is not None and not isinstance(name, str):
            name = None
        if claimed_date is not None:
            try:
                datetime.strptime(claimed_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                claimed_date = None

        return {"name": name, "claimed_date": claimed_date}
    except (GeminiNotConfigured, Exception) as exc:
        # Broad except is intentional here: any SDK/network/parsing failure
        # should degrade to the fallback, never crash the conversation.
        # A short console warning (not a full traceback) makes a real outage
        # visible during a demo without being alarming noise in normal use.
        print(f"[nlu] Gemini unavailable ({type(exc).__name__}: {exc}) — using rule-based fallback.")
        return _fallback_extract(message)
