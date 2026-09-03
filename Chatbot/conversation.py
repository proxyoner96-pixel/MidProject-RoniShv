"""
conversation.py
================
The chatbot's conversation state machine.

This module owns ALL the rules from the project brief:
  - Search by partial name; if ambiguous, ask for clarification (never guess).
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
"""

import os
import re
from datetime import datetime

from features import customers
from reply_builder import build_verified_reply

MAX_ATTEMPTS = int(os.environ.get("MAX_VERIFY_ATTEMPTS", "3"))

STAGE_NEW = "new"
STAGE_AWAIT_NAME_CLARIFICATION = "await_name_clarification"
STAGE_AWAIT_CONFIRM = "await_confirm"
STAGE_AWAIT_ID = "await_id"
STAGE_VERIFIED = "verified"
STAGE_BLOCKED = "blocked"

_AFFIRMATIVE = {"כן", "נכון", "yes", "כן.", "בטח", "אכן", "נכון מאוד", "yep", "ye", "y"}
_NEGATIVE = {"לא", "לא נכון", "no", "לא.", "nope"}


def initial_state() -> dict:
    return {"stage": STAGE_NEW, "attempts": 0}


def _reset(keep_greeting: bool = False) -> dict:
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


def _find_best_appointment(customer_id: int):
    """
    Return the single most relevant appointment for a verified customer, or
    None if they have none.

    Preference order: nearest upcoming Pending appointment; if there is no
    Pending appointment, the most recent Completed one; Cancelled
    appointments are ignored (an appointment the customer no longer has is
    not "their real appointment").

    Dates are stored as free-text DD/MM/YYYY strings in the DB, so we parse
    them here rather than relying on lexicographic SQL ordering.
    """
    history = customers.get_customer_history(customer_id)
    parsed = []
    for appt in history["appointments"]:
        if appt["status"] == "Cancelled":
            continue
        try:
            dt = datetime.strptime(
                f"{appt['appointment_date']} {appt['appointment_time']}", "%d/%m/%Y %H:%M"
            )
        except ValueError:
            continue
        parsed.append((dt, appt))

    if not parsed:
        return None

    now = datetime.now()
    pending_future = [(dt, a) for dt, a in parsed if a["status"] == "Pending" and dt >= now]
    if pending_future:
        pending_future.sort(key=lambda pair: pair[0])
        return pending_future[0][1]

    # No upcoming appointment — fall back to the most recent one overall.
    parsed.sort(key=lambda pair: pair[0], reverse=True)
    return parsed[0][1]


def handle_message(state: dict, text: str) -> tuple:
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
                names_list = ", ".join(c["name"] for c in candidates)
                return (
                    f"לא הצלחתי להתאים את זה לאחד מהשמות: {names_list}. "
                    "אפשר לכתוב את השם המלא בדיוק כפי שהוא?",
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
                names_list = ", ".join(m["name"] for m in matches)
                new_state = {
                    "stage": STAGE_AWAIT_NAME_CLARIFICATION,
                    "candidates": [dict(m) for m in matches],
                    "claimed_date": claimed_date,
                    "attempts": 0,
                }
                return (
                    f"נמצאו כמה לקוחות עם שם דומה: {names_list}. "
                    "מה השם המלא שלך?",
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
