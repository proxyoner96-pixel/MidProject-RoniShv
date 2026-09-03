"""
conftest.py
===========
Pytest setup shared by all tests in this folder.

Two jobs:
  1. Make the mid-project's `db` and `features` modules importable (they live
     in ../MidProject, one level up from here — same trick app.py uses).
  2. Provide a `fresh_db` fixture that points every test at a brand-new,
     throwaway SQLite file instead of the real appointments.db, so tests
     never depend on (or corrupt) the actual demo data, and can run in any
     order, any number of times, with no cleanup required.
"""

import os
import sys

MIDPROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "MidProject")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, MIDPROJECT_DIR)

import pytest


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """
    Point db.DB_PATH at a fresh temp file for every single test, and make
    sure Gemini is treated as "not configured" so tests exercise the
    deterministic rule-based fallback (no network calls, no flaky output).
    """
    import db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test_appointments.db"))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    db_module.init_db()
    yield db_module


@pytest.fixture
def seeded_customers(fresh_db):
    """
    A small, fixed set of customers covering every scenario in the brief:

      - "רותם ישראלי"  — unique name, has ONE upcoming appointment far in the
                          future (2099, so it's never accidentally "in the
                          past" no matter when this test suite runs).
      - "דני לוי" / "דני כהן" — share the first name "דני", so searching for
                          just "דני" must be ambiguous. "דני כהן" has NO
                          appointment at all (covers "customer with no open
                          appointment" in the same fixture).
    """
    from features import customers, appointments

    rotem_id = customers.add_customer("רותם ישראלי", "050-0000000", "r@example.com", "כתובת 1", "111111111")
    dani_levi_id = customers.add_customer("דני לוי", "050-1111111", "dl@example.com", "כתובת 2", "222222222")
    dani_cohen_id = customers.add_customer("דני כהן", "050-2222222", "dc@example.com", "כתובת 3", "333333333")

    appointments.add_appointment(
        customer_name="רותם ישראלי",
        service_type="אילוף",
        appointment_date="01/01/2099",
        appointment_time="12:00",
        customer_id=rotem_id,
    )
    appointments.add_appointment(
        customer_name="דני לוי",
        service_type="טיול",
        appointment_date="15/06/2099",
        appointment_time="09:00",
        customer_id=dani_levi_id,
    )
    # דני כהן intentionally has no appointment at all.

    return {
        "rotem_id": rotem_id,
        "dani_levi_id": dani_levi_id,
        "dani_cohen_id": dani_cohen_id,
    }
