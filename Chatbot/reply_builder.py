"""
reply_builder.py
=================
Builds the final, natural-language reply shown to a VERIFIED customer.

This is step 4 of the brief's architecture: after identity verification
succeeds, fetch the real appointment and phrase a friendly response that
highlights any gap between what the customer believes and what's actually
in the system.

Gemini is used only to phrase the sentence nicely — every fact in the
reply (name, date, time, service) comes from the database, never from the
model. If Gemini is unavailable, a clear deterministic Hebrew template is
used instead, so the bot never goes silent because of an API hiccup.
"""

from datetime import datetime

from features import customers
from gemini_client import generate, is_configured, GeminiNotConfigured

PHRASING_PROMPT = """You are a friendly Hebrew-speaking appointment-desk assistant.
Write ONE short, warm reply in Hebrew (2-4 sentences) based ONLY on the facts below.
Do not invent any information that is not in the facts. Do not use markdown.

Facts:
{facts}

If "claimed_date" and "actual_date" are both present and different, gently point out
the discrepancy and state the correct date and time clearly.
If there is no appointment at all, say so politely and suggest the customer contact
the business to schedule one.
"""


def _iso_to_display(iso_date: str) -> str:
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return iso_date


def _db_date_to_iso(db_date: str) -> str:
    try:
        return datetime.strptime(db_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _template_reply(customer_name: str, claimed_date: str, appointment) -> str:
    if appointment is None:
        return (
            f"מצאתי אותך, {customer_name}! עם זאת, לא נמצא תור פעיל על שמך במערכת כרגע. "
            "אם תרצה/י לקבוע תור, אשמח לעזור או שאפשר לפנות אלינו ישירות."
        )

    actual_date_display = appointment["appointment_date"]
    actual_time = appointment["appointment_time"]
    service = appointment["service_type"]
    actual_iso = _db_date_to_iso(appointment["appointment_date"])

    mismatch = bool(claimed_date and actual_iso and claimed_date != actual_iso)

    if mismatch:
        claimed_display = _iso_to_display(claimed_date)
        return (
            f"מצאתי אותך, {customer_name}! שימו לב: התור שלך בפועל הוא "
            f"ב-{actual_date_display} בשעה {actual_time} ({service}) — ולא ב-{claimed_display} "
            "כפי שציינת."
        )

    return (
        f"מצאתי אותך, {customer_name}! התור שלך הוא ב-{actual_date_display} "
        f"בשעה {actual_time} ({service})."
    )


def build_verified_reply(candidate_id: int, claimed_date: str, find_appointment) -> str:
    """
    Args:
        candidate_id:     the now-verified customer's ID.
        claimed_date:     ISO date (YYYY-MM-DD) the user claimed, or None.
        find_appointment: callable(customer_id) -> sqlite3.Row | None
                           (injected from conversation.py to avoid a circular import
                           and to keep this module easy to unit-test in isolation).
    """
    customer = customers.get_customer_by_id(candidate_id)
    customer_name = customer["name"] if customer else "לקוח/ה"
    appointment = find_appointment(candidate_id)

    if not is_configured():
        return _template_reply(customer_name, claimed_date, appointment)

    facts = {
        "customer_name": customer_name,
        "claimed_date": claimed_date,
        "actual_date": appointment["appointment_date"] if appointment else None,
        "actual_time": appointment["appointment_time"] if appointment else None,
        "service": appointment["service_type"] if appointment else None,
        "has_appointment": appointment is not None,
    }

    try:
        text = generate(PHRASING_PROMPT.format(facts=facts), json_mode=False).strip()
        if text:
            return text
        raise ValueError("Empty response from Gemini")
    except (GeminiNotConfigured, Exception) as exc:
        print(f"[reply_builder] Gemini unavailable ({type(exc).__name__}: {exc}) — using template reply.")
        return _template_reply(customer_name, claimed_date, appointment)
