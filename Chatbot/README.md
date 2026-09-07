# MidProject-RoniShv
# Appointments Management System
> **Mid-Course Python Project** — A robust, modular CLI appointment and CRM management system built with Python and SQLite.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Overview

The **Appointments Management System** is a command-line interface (CLI) application developed to streamline business scheduling, customer relationship management (CRM), and invoicing.

The **core system** (CLI, business logic, and database layer) is built entirely with Python's standard library — no external dependencies — and persists all operational data to a relational SQLite database. Its architecture strictly separates business logic, data persistence, and user presentation, ensuring high maintainability and full adaptability for any business domain via lightweight configuration.

The optional **Chatbot** extension (see below) adds a small set of third-party dependencies (Flask, python-dotenv, google-genai) — see `Chatbot/requirements.txt`.

---

## Key Features

- **End-to-End Appointment Scheduling**: Add, view, update, cancel, and delete appointments with real-time schedule conflict detection.
- **Customer & CRM Management**: Full customer lifecycle tracking with customer history, contact details, and linked records.
- **Lead Tracking & Automated Conversion**: Manage prospect pipelines and convert qualified leads into full customer accounts with a single command.
- **Automated Invoicing**: Auto-incrementing, collision-free invoice generation (`INV-0001`, `INV-0002`, ...) linked via foreign keys.
- **Strict Data Integrity**: Full schema validation, business hour enforcement, and foreign key cascades.

---

## Getting Started

### Prerequisites

- Python 3.10+
- For the chatbot only: a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### Run the CLI system

```bash
python main.py
```

The SQLite database (`appointments.db`) is created automatically on first run from `schema.sql` — no manual setup is needed.

### Run the Chatbot (web)

Full instructions in **[DEPLOY.md](DEPLOY.md)**. Quick start:

```bash
cd Chatbot
python -m venv .venv
.venv\Scripts\activate              # Windows CMD (PowerShell: Activate.ps1) | mac/linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env              # mac/linux: cp .env.example .env — then add GEMINI_API_KEY
python app.py                       # → http://localhost:5000
```

---

## Final Project — Verification & Appointments Chatbot

**🔗 Live demo: [ronishv.pythonanywhere.com](https://ronishv.pythonanywhere.com/)**

![Chatbot preview](demo/chatbot_preview.gif)

`Chatbot/` adds a natural-language web chatbot on top of this exact codebase (no new
CRUD, no duplicate data access): a customer types a free-text sentence, the bot
identifies them, verifies their ID number against the real record, and reports their
real appointment — correcting them if they misremembered the date. See
[`Chatbot/README.md`](Chatbot/README.md) for how it works,
[`DEPLOY.md`](DEPLOY.md) for running it locally or deploying it, and
[`demo/chatbot_demo.mp4`](demo/chatbot_demo.mp4) for a recorded end-to-end walkthrough.

---

## Testing & Verification

- Manual end-to-end verification scenarios: [`Chatbot/TEST_SCENARIOS.md`](Chatbot/TEST_SCENARIOS.md)
- Post-deployment health check: `GET /healthz` → `{"status": "ok"}`

---

## Security & Privacy Notes

- `.env` (containing `GEMINI_API_KEY`) is git-ignored and never committed.
- The database file (`appointments.db`) is git-ignored — customer records never enter version control.
- The chatbot never reveals any personal data before a successful ID-number verification, and blocks the conversation after too many failed attempts.
- The client-side conversation state contains only non-sensitive fields (stage, candidate id/name already typed by the user, claimed date, attempt counter).

---

## Project Structure

```text
MidProject-RoniShv/
├── main.py                 # Application entry point & configuration
├── Business.py             # Domain model holding business metadata & rules
├── db.py                   # Database connection manager (enforces PRAGMAs)
├── schema.sql              # Relational database DDL schema definitions
├── ui.py                   # Terminal UI, menus, ANSI stylers, & user input handlers
├── DEPLOY.md               # How to run locally & deploy/update the live demo
├── features/               # Modular feature package (Pure Business Logic)
│   ├── __init__.py
│   ├── appointments.py     # Appointment CRUD & conflict resolution logic
│   ├── customers.py        # Customer CRUD & appointment/invoice history
│   ├── invoice.py          # Sequential invoice generator & ledger
│   └── leads.py            # Lead lifecycle & customer conversion workflows
└── Chatbot/
    ├── app.py              # Flask server (chat page + /api/chat + /api/reset)
    ├── conversation.py     # Conversation state machine — identify → confirm → verify → answer
    ├── nlu.py              # Gemini-based free-text extraction (name + claimed date)
    ├── reply_builder.py    # Final natural-language reply, with real-data date comparison
    ├── gemini_client.py    # Single wrapper around the Gemini API (google-genai SDK)
    ├── requirements.txt    # Chatbot-only third-party dependencies
    ├── .env.example        # Template for GEMINI_API_KEY (real .env is git-ignored)
    ├── TEST_SCENARIOS.md   # Manual end-to-end verification scenarios
    └── templates/index.html
