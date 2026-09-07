MidProject-RoniShv
Appointments Management System
Mid-Course Python Project — A robust, modular CLI appointment & CRM management system built with Python and SQLite, extended with a natural-language verification chatbot.

Python Version
Database

Overview
The Appointments Management System is a command-line application for business scheduling, customer relationship management (CRM), and invoicing.

The core system (CLI, business logic, database layer) is built entirely with Python's standard library and persists all data to a relational SQLite database. Its architecture strictly separates business logic, data persistence, and user presentation.

The Chatbot extension (final project) adds a natural-language web chatbot on top of this exact codebase — no new CRUD, no duplicate data access — plus a small set of third-party dependencies (Flask, python-dotenv, google-genai), see Chatbot/requirements.txt.

Key Features
End-to-End Appointment Scheduling: Add, view, update, cancel, and delete appointments with real-time schedule conflict detection.
Customer & CRM Management: Full customer lifecycle tracking with history, contact details, and linked records.
Lead Tracking & Automated Conversion: Manage prospect pipelines and convert qualified leads into customers with a single command.
Automated Invoicing: Auto-incrementing, collision-free invoice generation (INV-0001, INV-0002, ...) linked via foreign keys.
Strict Data Integrity: Full schema validation, business hour enforcement, and foreign key cascades.
Verification Chatbot: Identity-verified appointment lookup via free-text conversation — never reveals personal data before a successful ID match.
Getting Started
Prerequisites
Python 3.10+
For the chatbot only: a free Gemini API key from Google AI Studio
Run the CLI system
cd MidProject
python main.py
The SQLite database (appointments.db) is created automatically on first run from schema.sql. To fill it with demo data:
python seed_data.py
Run the Chatbot (web)
Full instructions in DEPLOY.md. Quick start:
cd Chatbot
python -m venv .venv
.venv\Scripts\activate            # Windows | mac/linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # mac/linux: cp .env.example .env — then add GEMINI_API_KEY + FLASK_SECRET_KEY
python app.py                     # → http://localhost:5000
Final Project — Verification & Appointments Chatbot
🔗 Live demo: ronishv.pythonanywhere.com

Chatbot preview

A customer types a free-text sentence, the bot identifies them, verifies their ID number against the real record, and reports their real appointment — correcting them if they misremembered the date. See Chatbot/README.md, DEPLOY.md, and demo/chatbot_demo.mp4 for a recorded end-to-end walkthrough.

Testing
Automated tests cover the conversation state machine (identification, confirmation, verification, attempt limits):
cd Chatbot
pip install pytest
python -m pytest
cd Chatbot
pip install pytest
python -m pytest
Manual end-to-end scenarios: Chatbot/TEST_SCENARIOS.md. Post-deployment health check: GET /healthz → {"status": "ok"}.

Security & Privacy Notes
.env (containing GEMINI_API_KEY, FLASK_SECRET_KEY) is git-ignored and never committed.
The database file (appointments.db) is git-ignored — records never enter version control.
The chatbot never reveals personal data before a successful ID verification, and blocks the conversation after too many failed attempts.
The client-side conversation state contains only non-sensitive fields (stage, candidate id/name, claimed date, attempt counter).
Project Structure
MidProject-RoniShv/
├── README.md
├── DEPLOY.md               # How to run locally & deploy/update the live demo
├── .gitignore
├── demo/                   # Recorded walkthrough (mp4) + preview gif
├── MidProject/             # Core CLI system (standard library only)
│   ├── main.py             # Application entry point & configuration
│   ├── Business.py         # Domain model holding business metadata & rules
│   ├── db.py               # Database connection manager (enforces PRAGMAs)
│   ├── schema.sql          # Relational database DDL schema definitions
│   ├── ui.py               # Terminal UI, menus, ANSI stylers, & input handlers
│   ├── seed_data.py        # Fills the DB with demo data
│   └── features/           # Modular feature package (pure business logic)
│       ├── appointments.py # Appointment CRUD & conflict resolution
│       ├── customers.py    # Customer CRUD, history & identity verification
│       ├── invoice.py      # Sequential invoice generator & ledger
│       ├── leads.py        # Lead lifecycle & conversion workflows
│       └── stats.py        # Aggregated statistics
└── Chatbot/                # Final project extension
    ├── app.py              # Flask server (chat page + /api/chat + /api/reset + /healthz)
    ├── conversation.py     # Conversation state machine — identify → confirm → verify → answer
    ├── nlu.py              # Gemini-based free-text extraction (name + claimed date)
    ├── reply_builder.py    # Natural-language reply, with real-data date comparison
    ├── gemini_client.py    # Single wrapper around the Gemini API (google-genai SDK)
    ├── conftest.py         # Pytest fixtures
    ├── tests/              # Automated tests for the state machine
    ├── requirements.txt    # Chatbot-only third-party dependencies
    ├── .env.example        # Template (real .env is git-ignored)
    ├── TEST_SCENARIOS.md   # Manual end-to-end verification scenarios
    └── templates/index.html
