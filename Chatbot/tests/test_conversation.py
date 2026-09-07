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

Review-response notes:
  - Scenario 2 (ambiguous name) now asserts the bot does NOT echo any
    customer names to an unverified user — only asks for the full name.
  - Scenario 2 also checks that no appointment details leak in the
    clarification reply.
  - A sanity-check test guards the fixture itself, so the suite fails fast
    (with a clear reason) if the seeded data is missing rather than
    silently passing "on empty".
"""

import conversation


def test_fixture_sanity_seeded_data_is_present(seeded_customers):
    """Guard the fixture: fail fast with a clear reason if the seeded data
    is missing, so the rest of the suite never passes 'on empty'."""
    from features import customers, appointments

    all_customers = customers.search_customers_by_name("דני")
    assert len(all_customers) >= 2, (
        "Fixture problem: expected at least 2 customers named דני "
        "(ambiguous-name scenario depends on them)"
    )

    rotem = customers.search_customers_by_name("רותם")
    assert len(rotem) == 1, "Fixture problem: expected exactly 1 customer named רותם"

    history = customers.get_customer_history(seeded_customers["rotem_id"])
    assert len(history["appointments"]) >= 1, (
        "Fixture problem: רותם must have at least one appointment for the "
        "correction scenario"
    )


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
    one, never silently pick one.

    Privacy (review feedback): the clarification reply must NOT echo the
    other customers' names — the user is still unverified, and revealing
    which customers exist is information leakage. The bot must simply ask
    for the full name.
    """
    state = conversation.initial_state()

    reply, state = conversation.handle_message(state, "קוראים לי דני")
    assert state["stage"] == conversation.STAGE_AWAIT_NAME_CLARIFICATION
    # No customer names may be echoed to an unverified user.
    assert "דני לוי" not in reply
    assert "דני כהן" not in reply
    # And no appointment details either (review feedback: check for leaks here too).
    assert "2099" not in reply and "09:00" not in reply and "טיול" not in reply
    # The bot must still move the conversation forward — ask for the full name.
    assert "שם המלא" in reply

    # The full name resolves to exactly one candidate → confirmation stage.
    reply, state = conversation.handle_message(state, "דני כהן")
    assert state["stage"] == conversation.STAGE_AWAIT_CONFIRM
    assert "דני כהן" in reply


def test_ambiguous_name_wrong_full_name_keeps_asking_without_leaking(seeded_customers):
    """If the user can't produce a full name that matches, the bot keeps
    asking — still without ever revealing which candidates exist."""
    state = conversation.initial_state()
    _, state = conversation.handle_message(state, "קוראים לי דני")
    assert state["stage"] == conversation.STAGE_AWAIT_NAME_CLARIFICATION

    reply, state = conversation.handle_message(state, "דני לא קיים בכלל")
    assert state["stage"] == conversation.STAGE_AWAIT_NAME_CLARIFICATION
    assert "דני לוי" not in reply and "דני כהן" not in reply


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