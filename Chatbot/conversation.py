"""
conversation.py
================
The chatbot's conversation state machine.

This module owns ALL the rules from the project brief:
  - Search by partial name; if ambiguous, ask for the full name WITHOUT
    revealing which customers exist, and never guess.
  - Confirm the matched name before asking for anything sensitive.
  - Never reveal any personal data (date, time, anything) before a
    successful ID-number match against the real data.
  - Limit verification attempts (MAX_ATTEMPTS) and then block politely.
  - Handle: name not found, customer with no appointment, wrong ID.
  - After verification, fetch the REAL appointment and, if the user claimed
    a wrong date, correct them using the real data.

`handle_message(state, text)` is a pure function: given the current
conversation state (a plain JSON-serializable dict — easy to store in a
Flask session cookie) and the user's new message, it returns
(reply_text, new_state). It never touches Flask directly, which makes it
trivial to unit-test without spinning up a web server.

IMPORTANT — state hygiene:
The state dict is stored client-side in the Flask session cookie, which is
*signed but not encrypted* — the user can decode and read it. Therefore the
state must contain ONLY non-sensitive fields: stage name, candidate id, the
candidate's name (which the user already typed themselves), the user's own
claimed date, and the attempt counter. Never store ID numbers, phone
numbers, emails, or raw DB rows here.
"""

import logging
import os
import re
from datetime import datetime
from enum import Enum
from typing import Tuple

from features import customers
from reply_builder import build_verified_reply

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = int(os.environ.get("MAX_VERIFY_ATTEMPTS", "3"))


class Stage(str, Enum):
    """
    All possible conversation stages.

    Subclasses str so that values survive JSON round-trips in the session
    cookie and compare equal to their plain strings ('new' == Stage.NEW).
    (Review feedback: enum-based state management instead of bare strings.)
    """
    NEW = "new"
    AWAIT_NAME_CLARIFICATION = "await_name_clarification"
    AWAIT_CONFIRM = "await_confirm"
    AWAIT_ID = "await_id"
    VERIFIED = "verified"
    BLOCKED = "blocked"


# Backwards-compatible aliases — existing code and tests import these names.
STAGE_NEW = Stage.NEW
STAGE_AWAIT_NAME_CLARIFICATION = Stage.AWAIT_NAME_CLARIFICATION
STAGE_AWAIT_CONFIRM = Stage.AWAIT_CONFIRM
STAGE_AWAIT_ID = Stage.AWAIT_ID
STAGE_VERIFIED = Stage.VERIFIED
STAGE_BLOCKED = Stage.BLOCKED

# The DB stores Israeli-local wall-clock times, but the production server
# (PythonAnywhere) runs in UTC. All "upcoming vs past" comparisons are
# therefore done in Israel's timezone. If the platform has no timezone
# database (e.g. Windows without the `tzdata` pip package), we fall back to
# naive local time — same behaviour as before, just less precise.
try:
    from zoneinfo import ZoneInfo
    BUSINESS_TZ = ZoneInfo("Asia/Jerusalem")
except Exception:  # pragma: no cover
    BUSINESS_TZ = None

# Hebrew answers that merely *start* with כן/לא ("כן.", "לא נכון", ...) are
# covered by the prefix matching in _is_affirmative / _is_negative, so the
# sets only need the standalone variants.
_AFFIRMATIVE = {"נכון", "נכון מאוד", "בטח", "אכן", "yes", "yep", "ye", "y"}
_NEGATIVE = {"no", "nope"}


def initial_state() -> dict:
    return {"stage": STAGE_NEW, "attempts": 0}


def _reset() -> dict:
    """Fresh conversation state — used whenever we abandon the current path."""
    return initial_state()


def _is_affirmative(text: str) -> bool:
    t = text.strip().lower()
    return t in _AFFIRMATIVE or t.startswith("כן")


def _is_negative(text: str) -> bool:
    t = text.strip().lower()
    return t in _NEGATIVE or t.startswith("לא")


def _extract_id_number(text: str) -> str:
    """Pull the longest run of digits out of free text (users sometimes type
    'ת.ז. 200000008' or add spaces/dashes)."""
    digits = re.sub(r"\D", "", text)
    return digits


def _parse_appointment_dt(appt):
    """Parse an appointment's date+time (free-text 'DD/MM/YYYY HH:MM' in the
    DB) into a datetime anchored to the business timezone, or None if the
    stored text is unparsable (logged, not silently swallowed)."""
    try:
        dt = datetime.strptime(
            f"{appt['appointment_date']} {appt['appointment_time']}",
            "%d/%m/%Y %H:%M",
        )
    except (ValueError, TypeError):
        logger.warning(
            "Skipping appointment with unparsable date/time: %r / %r",
            appt["appointment_date"],
            appt["appointment_time"],
        )
        return None
    if BUSINESS_TZ is not None:
        dt = dt.replace(tzinfo=BUSINESS_TZ)
    return dt


def _find_best_appointment(customer_id: int):
    """
    Return the single most relevant appointment for a verified customer, or
    None if they have none.

    Preference order: nearest upcoming Pending appointment; if there is no
    Pending appointment, the most recent one that isn't Cancelled (an
    appointment the customer no longer has is not "their real appointment").

    Dates are stored as free-text DD/MM/YYYY strings in the DB, so we parse
    them here rather than relying on lexicographic SQL ordering, and compare
    against "now" in Israel's timezone (see BUSINESS_TZ above).
    """
    history = customers.get_customer_history(customer_id)
    parsed = []
    for appt in history["appointments"]:
        if appt["status"] == "Cancelled":
            continue
        dt = _parse_appointment_dt(appt)
        if dt is None:
            continue
        parsed.append((dt, appt))

    if not parsed:
        return None

    now = datetime.now(BUSINESS_TZ) if BUSINESS_TZ else datetime.now()
    pending_future = [(dt, a) for dt, a in parsed if a["status"] == "Pending" and dt >= now]
    if pending_future:
        pending_future.sort(key=lambda pair: pair[0])
        return pending_future[0][1]

    # No upcoming appointment — fall back to the most recent one overall.
    parsed.sort(key=lambda pair: pair[0], reverse=True)
    return parsed[0][1]


def handle_message(state: dict, text: str) -> Tuple[str, dict]:
    """
    Advance the conversation by one turn.

    Args:
        state: the previous conversation state (see initial_state()).
        text:  the user's new message.

    Returns:
        (reply_text, new_state)
    """
    text = (text or "").strip()
    if not text:
        return "לא קיבלתי הודעה. אפשר לכתוב משהו?", state

    stage = state.get("stage", STAGE_NEW)

    # ── Blocked: no further interaction until a human takes over ──────────
    if stage == STAGE_BLOCKED:
        return (
            "השיחה חסומה זמנית עקב יותר מדי ניסיונות אימות שגויים, "
            "מטעמי אבטחה. אנא פנה/י אלינו ישירות בטלפון או במייל.",
            state,
        )

    # ── New conversation, or clarifying an ambiguous name ──────────────────
    if stage in (STAGE_NEW, STAGE_AWAIT_NAME_CLARIFICATION):
        if stage == STAGE_AWAIT_NAME_CLARIFICATION:
            candidates = state.get("candidates", [])
            match = next(
                (c for c in candidates if c["name"].strip() == text.strip()), None
            )
            if match is None:
                # Try a looser partial match against the *candidate list only*
                # (still never guessing among the wider customer table).
                loose = [c for c in candidates if text.strip() in c["name"]]
                if len(loose) == 1:
                    match = loose[0]
            if match is None:
                # Privacy (review feedback): never echo the candidates' names.
                return (
                    "לא הצלחתי להתאים את זה. אפשר לכתוב את השם המלא "
                    "בדיוק כפי שהוא רשום במערכת?",
                    state,
                )
            candidate = match
            claimed_date = state.get("claimed_date")
        else:
            from nlu import extract_name_and_date  # local import avoids a hard dep at module load

            extracted = extract_name_and_date(text)
            name = extracted.get("name")
            claimed_date = extracted.get("claimed_date")

            if not name:
                return (
                    "לא הצלחתי לזהות שם בהודעה. אפשר לכתוב, לדוגמה: "
                    "\"קוראים לי דני ויש לי תור ב-05/01/2026\"?",
                    state,
                )

            matches = customers.search_customers_by_name(name)
            if len(matches) == 0:
                return (
                    f"לא מצאתי לקוח בשם \"{name}\" במערכת. אפשר לבדוק את האיות "
                    "או לנסות עם השם המלא?",
                    _reset(),
                )
            if len(matches) > 1:
                # Privacy (review feedback): do NOT reveal which customers
                # exist — just ask for the full name. The candidate list
                # (id+name only, see state hygiene above) still lives in the
                # state so the next turn can match against it.
                new_state = {
                    "stage": STAGE_AWAIT_NAME_CLARIFICATION,
                    "candidates": [{"id": m["id"], "name": m["name"]} for m in matches],
                    "claimed_date": claimed_date,
                    "attempts": 0,
                }
                return (
                    "נמצאו כמה לקוחות עם שם דומה. מה השם המלא שלך? "
                    "(שם פרטי ושם משפחה)",
                    new_state,
                )
            candidate = matches[0]

        new_state = {
            "stage": STAGE_AWAIT_CONFIRM,
            "candidate_id": candidate["id"],
            "candidate_name": candidate["name"],
            "claimed_date": claimed_date,
            "attempts": 0,
        }
        return f"קוראים לך {candidate['name']}?", new_state

    # ── Confirming the matched identity (name only — not yet verified) ────
    if stage == STAGE_AWAIT_CONFIRM:
        if _is_affirmative(text):
            new_state = dict(state)
            new_state["stage"] = STAGE_AWAIT_ID
            return "מה תעודת הזהות שלך? (לצורך אימות בלבד)", new_state
        if _is_negative(text):
            return (
                "בסדר, לא ממשיכים עם השם הזה. אפשר לכתוב מחדש את השם המלא שלך?",
                _reset(),
            )
        return "לא הבנתי — זה כן או לא?", state

    # ── Waiting for the ID number — the actual verification gate ──────────
    if stage == STAGE_AWAIT_ID:
        id_number = _extract_id_number(text)
        if len(id_number) < 5:
            return "זה לא נראה כמו מספר תעודת זהות תקין. אפשר לשלוח רק את הספרות?", state

        candidate_id = state["candidate_id"]
        if customers.verify_identity(candidate_id, id_number):
            reply = build_verified_reply(
                candidate_id=candidate_id,
                claimed_date=state.get("claimed_date"),
                find_appointment=_find_best_appointment,
            )
            return reply, {"stage": STAGE_VERIFIED, "candidate_id": candidate_id, "attempts": 0}

        attempts = state.get("attempts", 0) + 1
        if attempts >= MAX_ATTEMPTS:
            return (
                "בוצעו יותר מדי ניסיונות אימות שגויים. מטעמי אבטחה השיחה "
                "נחסמת כעת. אנא פנה/י אלינו ישירות.",
                {"stage": STAGE_BLOCKED},
            )
        new_state = dict(state)
        new_state["attempts"] = attempts
        remaining = MAX_ATTEMPTS - attempts
        return (
            f"תעודת הזהות שגויה, לא הצלחתי לאמת אותך. נותרו {remaining} ניסיונות.",
            new_state,
        )

    # ── Already verified — allow a fresh lookup without losing the session ─
    if stage == STAGE_VERIFIED:
        if any(word in text for word in ("שיחה חדשה", "לקוח אחר", "להתחיל מחדש")):
            return "בטח, מתחילים שיחה חדשה. במה אוכל לעזור?", _reset()
        reply = build_verified_reply(
            candidate_id=state["candidate_id"],
            claimed_date=None,
            find_appointment=_find_best_appointment,
        )
        return reply, state

    # Should not normally be reached.
    return "מצטער, קרתה תקלה בשיחה. בוא/י נתחיל מחדש — מה השם שלך?", _reset()