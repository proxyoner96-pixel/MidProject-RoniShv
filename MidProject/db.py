"""
db.py
=====
Handles all SQLite database connectivity for the Appointments Management System.

Responsibilities:
  - DB_PATH: single constant defining where the database file lives.
  - get_connection(): opens a connection with foreign keys enforced and
    row_factory set so rows behave like dictionaries.
  - init_db(): reads schema.sql and creates all tables if they don't exist yet.
"""

import sqlite3
import os

# Path to the SQLite database file.
# Located in the same directory as this file.
# NOTE: this file is generated automatically on first run (see init_db) and
# must stay out of version control (see .gitignore) — it holds real records.
DB_PATH = os.path.join(os.path.dirname(__file__), "appointments.db")

# Path to the SQL schema file (relative to this file).
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

# How long (seconds) a connection waits for a database lock before raising
# "database is locked". The web chatbot can receive concurrent requests;
# without a timeout, two simultaneous writes could crash one of them.
DB_TIMEOUT_SECONDS = 10


def get_connection() -> sqlite3.Connection:
    """
    Open and return a connection to the SQLite database.

    Settings applied to every connection:
      - timeout=DB_TIMEOUT_SECONDS : wait instead of failing on transient locks.
      - PRAGMA foreign_keys = ON  : enforce ON DELETE CASCADE / SET NULL rules.
        (SQLite applies this per-connection, so it must be set every time.)
      - row_factory = sqlite3.Row : rows are accessible by column name (like dicts).
    """
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT_SECONDS)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_customers_id_number_column(conn: sqlite3.Connection) -> None:
    """
    Defensive migration: guarantee `customers.id_number` exists.

    `CREATE TABLE IF NOT EXISTS` (used in init_db) does nothing to a table that
    already exists — so if an older copy of appointments.db (from before the
    chatbot's identity-verification feature) is ever restored, re-synced, or
    checked out on top of the current schema.sql, the app would crash with
    "no such column: id_number" instead of just... having the column. This
    function makes startup self-healing regardless of which appointments.db
    happens to be on disk.
    """
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(customers)").fetchall()]
    if "id_number" not in columns:
        conn.execute("ALTER TABLE customers ADD COLUMN id_number TEXT")

    # Backfill any customer left without an id_number (e.g. rows that existed
    # before this column was added) so identity verification always has
    # something concrete to check, instead of every such customer being
    # permanently unverifiable.
    conn.execute(
        "UPDATE customers SET id_number = printf('900%06d', id) "
        "WHERE id_number IS NULL OR TRIM(id_number) = ''"
    )


def init_db() -> None:
    """
    Read schema.sql and execute it to create all tables (IF NOT EXISTS),
    then run any small defensive migrations for columns added after the
    original schema (see _ensure_customers_id_number_column).

    Called once at startup from main.py / the chatbot's app.py — this is how
    a fresh deployment ends up with a working database without shipping one.
    """
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(
            f"schema.sql not found at {SCHEMA_PATH}. "
            "Make sure it sits next to db.py (it is part of the repository)."
        )

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()

    # NOTE: `with sqlite3.connect(...)` only commits/rolls back — it does NOT
    # close the connection, so we close it explicitly.
    conn = get_connection()
    try:
        conn.executescript(schema)
        _ensure_customers_id_number_column(conn)
        conn.commit()
    finally:
        conn.close()