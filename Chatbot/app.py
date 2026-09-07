"""
app.py
======
Flask entry point for the verification chatbot.

This app does NOT reimplement any data access — it imports the existing
`db` and `features` modules from ../MidProject and talks to the very same
appointments.db. That's the whole point of the final project: a
conversation layer on top of the mid-project, not a new system.

Run locally:
    pip install -r requirements.txt
    copy .env.example .env      # then edit .env: add GEMINI_API_KEY + FLASK_SECRET_KEY
    python app.py

Then open http://localhost:5000
"""

import os
import sys

from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────
# Make the existing mid-project code importable (db.py, features/*.py live
# in ../MidProject, one level up from this file).
# ─────────────────────────────────────────────────────────────────────────
MIDPROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "MidProject")
sys.path.insert(0, MIDPROJECT_DIR)

from db import init_db  # noqa: E402  (import after sys.path tweak is intentional)
import conversation  # noqa: E402

app = Flask(__name__)

# ── Session security ─────────────────────────────────────────────────────
# The session cookie is *signed, not encrypted*: it protects the conversation
# state from tampering, but only if the signing key is secret. Since the
# verified stage + candidate_id live in that cookie, a guessable key would let
# anyone forge a "verified" session and bypass ID verification entirely.
# FLASK_SECRET_KEY is therefore REQUIRED — never ship a default fallback.
# Generate one:  python -c "import secrets; print(secrets.token_hex(32))"
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "").strip()
if not app.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is not set. Add it to .env "
        '(generate: python -c "import secrets; print(secrets.token_hex(32))")'
    )

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Enable on the HTTPS deployment: set FLASK_COOKIE_SECURE=1 in the server's .env
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_COOKIE_SECURE", "0") == "1",
)

# Make sure the database and tables exist before the first request.
# Idempotent: CREATE TABLE IF NOT EXISTS + defensive migrations (see db.py).
init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    user_message = (payload.get("message") or "").strip()

    if "conv_state" not in session:
        session["conv_state"] = conversation.initial_state()

    if not user_message:
        return jsonify({"reply": "אפשר לכתוב הודעה?", "stage": session["conv_state"].get("stage")})

    try:
        reply, new_state = conversation.handle_message(session["conv_state"], user_message)
    except Exception:
        # A transient failure (e.g. the Gemini API is temporarily down) must
        # not crash the request or corrupt the conversation: keep the current
        # state unchanged and let the user simply retry.
        app.logger.exception("handle_message failed")
        return jsonify({
            "reply": "ארעה תקלה זמנית בעיבוד ההודעה. נסו שוב בעוד רגע.",
            "stage": session["conv_state"].get("stage"),
        })

    session["conv_state"] = new_state
    session.modified = True

    return jsonify({"reply": reply, "stage": new_state.get("stage")})


@app.route("/api/reset", methods=["POST"])
def reset():
    session["conv_state"] = conversation.initial_state()
    session.modified = True
    return jsonify({"ok": True})


@app.route("/healthz")
def healthz():
    """Simple liveness check — handy for the deployment platform + DEPLOY.md."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Debug is opt-in (FLASK_DEBUG=1), never on by default: the Werkzeug
    # debugger can execute arbitrary code from error pages.
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="127.0.0.1", port=port, debug=debug)