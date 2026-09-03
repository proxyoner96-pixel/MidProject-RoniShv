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
    copy .env.example .env      # then edit .env and add your GEMINI_API_KEY
    python app.py

Then open http://localhost:5000
"""

import os
import sys
import uuid

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
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

# Make sure the database and tables exist before the first request.
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
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    if not user_message:
        return jsonify({"reply": "אפשר לכתוב הודעה?", "stage": session["conv_state"].get("stage")})

    reply, new_state = conversation.handle_message(session["conv_state"], user_message)
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
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
