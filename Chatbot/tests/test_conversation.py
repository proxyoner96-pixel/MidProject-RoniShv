"""
tests/test_conversation.py
===========================
Automated checks for the chatbot's conversation state machine, covering the
five mandatory scenarios from the project brief plus the security rules
around them. Every test runs against an isolated, throwaway SQLite database
(see conftest.py) and with Gemini disabled, so results are deterministic and
require no network access or API key.

Run with:
    pytest
(from the Chatbot/ directory — conftest.py there sets up the import paths).
"""

import conversation


def test_unique_name_with_wrong_claimed_date_gets_corrected(seeded_customers):
    """Scenario 1: unique name + wrong date → bot corrects with the real
    date/time once identity is verified, and never before."""
    state = conversation.initial_state()

    reply, state = conversation.handle_message(state, "קוראים לי רותם ויש לי תור ב-05.05.2030")
    assert state["stage"] == conversation.STAGE_AWAIT_CONFIRM
    assert "רותם ישראלי" in reply
    # No appointment details may appear before confirmation, let alone verification.
    assert "2099" not in reply and "12:00" not in reply

    reply, state = conversation.handle_message(state, "כן")
    assert state["stage"] == conversation.STAGE_AWAIT_ID
    assert "2099" not in reply  # still not verified — still no data.

    reply, state = conversation.handle_message(state, "111111111")
    assert state["stage"] == conversation.STAGE_VERIFIED
    assert "01/01/2099" in reply and "12:00" in reply  # the REAL appointment
    assert "05/05/2030" in reply  # the (wrong) date the user claimed, for the correction


def test_ambiguous_first_name_asks_for_clarification_not_a_guess(seeded_customers):
    """Scenario 2: two customers share a first name → the bot must ask which
    one, never silently pick one."""
    state = conversation.initial_state()

    reply, state = conversation.handle_message(state, "קוראים לי דני")
    assert state["stage"] == conversation.STAGE_AWAIT_NAME_CLARIFICATION
    assert "דני לוי" in reply and "דני כהן" in reply

    reply, state = conversation.handle_message(state, "דני כהן")
    assert state["stage"] == conversation.STAGE_AWAIT_CONFIRM
    assert "דני כהן" in reply


def test_verified_customer_with_no_appointment(seeded_customers):
    """Scenario 4: an existing, verified customer with zero appointments must
    get a clear "no appointment" answer, not an error or a guess."""
    state = conversation.initial_state()
    _, state = conversation.handle_message(state, "קוראים לי דני")
    _, state = conversation.handle_message(state, "דני כהן")
    _, state = conversation.handle_message(state, "כן")
    reply, state = conversation.handle_message(state, "333333333")

    assert state["stage"] == conversation.STAGE_VERIFIED
    assert "לא נמצא תור" in reply


def test_unknown_name_is_reported_without_crashing(seeded_customers):
    """Scenario 5: a name that doesn't exist anywhere in the system."""
    state = conversation.initial_state()
    reply, state = conversation.handle_message(state, "קוראים לי קסנופון פלוני")

    assert state["stage"] == conversation.STAGE_NEW
    assert "לא מצאתי" in reply
    assert "קסנופון" in reply


def test_wrong_id_number_never_leaks_data_and_locks_after_max_attempts(seeded_customers):
    """Scenario 3 + attempt-limit rule: wrong ID → polite refusal with zero
    leaked data, and after MAX_ATTEMPTS wrong tries the chat locks — even a
    subsequently CORRECT id number must then be refused."""
    state = conversation.initial_state()
    _, state = conversation.handle_message(state, "קוראים לי רותם ויש לי תור ב-05.05.2030")
    _, state = conversation.handle_message(state, "כן")
    assert state["stage"] == conversation.STAGE_AWAIT_ID

    wrong_ids = ["999999999", "888888888", "777777777"]
    for i, wrong_id in enumerate(wrong_ids, start=1):
        reply, state = conversation.handle_message(state, wrong_id)
        # No appointment fact may ever appear in a failed-verification reply.
        assert "2099" not in reply and "12:00" not in reply and "אילוף" not in reply
        if i < conversation.MAX_ATTEMPTS:
            assert state["stage"] == conversation.STAGE_AWAIT_ID
        else:
            assert state["stage"] == conversation.STAGE_BLOCKED

    # Even the CORRECT id, after lockout, must be refused — not silently accepted.
    reply, state = conversation.handle_message(state, "111111111")
    assert state["stage"] == conversation.STAGE_BLOCKED
    assert "2099" not in reply and "12:00" not in reply


def test_id_number_extraction_ignores_punctuation_and_spacing(seeded_customers):
    """Users often type 'ת.ז. 111-111-111' — the digits should still match."""
    state = conversation.initial_state()
    _, state = conversation.handle_message(state, "קוראים לי רותם")
    _, state = conversation.handle_message(state, "כן")

    reply, state = conversation.handle_message(state, "ת.ז. 111-111-111")
    assert state["stage"] == conversation.STAGE_VERIFIED
    assert "01/01/2099" in reply


def test_too_short_input_is_rejected_before_touching_the_database(seeded_customers):
    """A clearly invalid ID (too few digits) shouldn't count as an attempt at
    all, and obviously shouldn't verify anyone."""
    state = conversation.initial_state()
    _, state = conversation.handle_message(state, "קוראים לי רותם")
    _, state = conversation.handle_message(state, "כן")

    reply, state = conversation.handle_message(state, "12")
    assert state["stage"] == conversation.STAGE_AWAIT_ID
    assert state.get("attempts", 0) == 0  # not counted as a real attempt
