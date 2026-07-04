# Kiko AI Chatbot

A conversational AI chatbot built with **FastAPI**, **SQLite**, and **NVIDIA NIM** (LLaMA 3.1 8B). Handles greetings, FAQs, general queries, and escalates to a human agent when needed.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Chat Flow Logic](#chat-flow-logic)
- [Database Schema](#database-schema)
- [FAQ System](#faq-system)
- [Rate Limiting](#rate-limiting)
- [Human Handoff](#human-handoff)
- [Known Limitations](#known-limitations)
---

## Features

- **AI-powered responses** via NVIDIA NIM (LLaMA 3.1 8B Instruct)
- **Intent classification** — greeting, farewell, faq, general_query, complaint, human_agent_request, unknown
- **FAQ fuzzy matching** — in-memory cached, difflib-based (cutoff 0.55)
- **Rule-based fallback** — keyword engine if AI call fails
- **Human handoff** — triggers on explicit request or 3 consecutive unknown intents
- **Session management** — UUID-keyed chat sessions with persistent history
- **Rate limiting** — 20 messages/minute per session (in-memory)
- **REST API** — fully documented via FastAPI auto-docs (`/docs`)
---

## Architecture

```
User Request
     │
     ▼
FastAPI (main.py)
     │
     ├── Rate Limiter (api/middleware/rate_limiter.py)
     │
     ▼
Chatbot Orchestrator (core/chatbot.py)
     │
     ├─1─ Explicit human keyword? ──► Handoff
     │
     ├─2─ FAQ Cache match? ──────────► Return FAQ answer
     │         (core/faq_matcher.py)
     │
     ├─3─ NVIDIA NIM AI call ────────► Intent + Response JSON
     │         (core/ai_engine.py)
     │
     └─4─ Rule-based fallback ───────► Keyword-matched response
               (core/rule_engine.py)
     │
     ▼
SQLite DB  (database/chatbot.db)
  - Save user message
  - Save bot response
  - Update session intent counters
```

---

## Project Structure

```
chatbot-project/
├── main.py                        # FastAPI app entry point, CORS, router mounting, static mount
├── config.py                      # Settings loaded from .env
├── seed_faqs.py                   # One-time DB seeder (15 default FAQs)
├── .env                           # Local secrets (not committed)
├── .env.example                   # Template for required env vars
│
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── chat.py                # POST /api/chat, GET /api/chat/history/{session_id}
│   │   ├── faq.py                 # CRUD for FAQs
│   │   ├── session.py             # POST /api/session/new
│   │   └── health.py              # GET /api/health
│   └── middleware/
│       └── rate_limiter.py        # 20 req/min per session_id
│
├── core/
│   ├── __init__.py
│   ├── chatbot.py                 # Main orchestration logic
│   ├── ai_engine.py               # NVIDIA NIM API client + JSON parsing
│   ├── faq_matcher.py             # Cached fuzzy FAQ lookup
│   └── rule_engine.py             # Keyword fallback responses
│
├── database/
│   ├── __init__.py
│   ├── db.py                      # Async SQLAlchemy engine + session factory
│   ├── models.py                  # ChatSession, Message, FAQ ORM models
│   └── chatbot.db                 # SQLite database file
│
└── static/                        # Frontend, served at / via FileResponse, assets via /static mount
    ├── index.html                 # Markup only — links css/js below
    ├── css/
    │   └── styles.css             # All chat widget styling, design tokens, dark mode
    └── js/
        └── app.js                 # Session init, send/receive, typing indicator, handoff UI
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| ASGI server | Uvicorn |
| AI model | NVIDIA NIM — `meta/llama-3.1-8b-instruct` |
| AI client | `openai` Python SDK (pointed at NVIDIA base URL) |
| Database | SQLite via `aiosqlite` |
| ORM | SQLAlchemy (async) |
| FAQ matching | Python `difflib.get_close_matches` |
| Python version | 3.14 (project uses `str | None` union syntax) |

---

## Getting Started

### 1. Clone / unzip the project

```bash
unzip chatbot-project-fixed.zip
cd chatbot-fixed
```

### 2. Create and activate a virtual environment

```bash
python -m venv env
# Windows
env\Scripts\activate
# macOS / Linux
source env/bin/activate
```

### 3. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy aiosqlite openai python-dotenv
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env and set your NVIDIA_API_KEY
```

### 5. Seed the database

```bash
python seed_faqs.py
```

This creates `database/chatbot.db` and inserts 15 default FAQs. Safe to re-run — skips if FAQs already exist.

### 6. Run the server

```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Open the app

- **Frontend:** http://localhost:8000
- **API docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

> Always load the frontend through the running server (`http://localhost:8000/`), not by opening `static/index.html` directly as a `file://` path — asset links and API calls are root-relative and require the FastAPI server.

---

## Configuration

All config is read from `.env` via `config.py`.

| Variable | Required | Default | Description |
|---|---|---|---|
| `NVIDIA_API_KEY` | ✅ Yes | — | API key from [build.nvidia.com](https://build.nvidia.com) |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./database/chatbot.db` | SQLAlchemy async DB URL |
| `DEBUG` | No | `True` | Enables SQLAlchemy query logging |
| `ALLOWED_ORIGINS` | No | `http://localhost:8000,http://127.0.0.1:8000` | Comma-separated CORS whitelist |

For production, set `DEBUG=False` and restrict `ALLOWED_ORIGINS` to your actual frontend domain.

---

## API Reference

### Chat

#### `POST /api/chat/`

Send a message and receive a bot response.

**Request body:**
```json
{
  "session_id": "abc-123",
  "message": "What is your return policy?",
  "user_name": "Billu"
}
```

**Response:**
```json
{
  "session_id": "abc-123",
  "bot_name": "Kiko",
  "response": "You can return any product within 30 days of receipt...",
  "intent": "faq",
  "handoff": false,
  "timestamp": "2026-06-26T00:10:00Z"
}
```

**Intent values:** `greeting` · `farewell` · `faq` · `general_query` · `complaint` · `human_agent_request` · `unknown`

#### `GET /api/chat/history/{session_id}`

Returns full message history for a session.

```json
[
  { "role": "user", "content": "Hello", "timestamp": "..." },
  { "role": "bot",  "content": "Hi! I'm Kiko...", "timestamp": "..." }
]
```

Returns `404` if session not found.

---

### Session

#### `POST /api/session/new`

Creates a new chat session. Call this before your first chat message.

```json
{ "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479" }
```

---

### FAQs

#### `GET /api/faqs/`

Returns all FAQ entries.

#### `POST /api/faqs/`

Add a new FAQ. Automatically invalidates the in-memory FAQ cache.

```json
{ "question": "Do you have a loyalty program?", "answer": "Yes! Earn points on every purchase." }
```

#### `DELETE /api/faqs/{faq_id}`

Delete an FAQ by ID. Also invalidates cache.

---

### Health

#### `GET /api/health/`

```json
{ "status": "ok", "service": "Kiko Chatbot API" }
```

---

## Chat Flow Logic

`core/chatbot.py` is the orchestrator. For every incoming message it executes these steps in order:

```
1. Ensure session exists in DB (create if new)
2. Save user message to DB
3. Check for human handoff keywords ("human", "agent", "real person")
   └─ Yes → set intent=human_agent_request, handoff=True, skip AI
4. Check FAQ cache (fuzzy match, cutoff 0.55)
   └─ Hit → return FAQ answer, intent=faq
5. Fetch last 10 messages from DB for context
6. Call NVIDIA NIM AI → expect JSON { intent, response }
   └─ Success → use AI intent + response
   └─ Failure → fall through to rule engine
7. Rule engine keyword match (greeting / farewell / human / unknown)
8. Track unknown_intent_count on session
   └─ 3 consecutive unknowns → force handoff=True
9. Save bot response to DB
10. Return response payload
```

---

## Database Schema

### `chat_sessions`

| Column | Type | Notes |
|---|---|---|
| `session_id` | String (PK) | UUID, auto-generated |
| `created_at` | DateTime | Auto-set on creation |
| `unknown_intent_count` | Integer | Consecutive unknowns; resets on any successful intent |

### `messages`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `session_id` | String (FK) | References `chat_sessions.session_id` |
| `role` | String | `"user"` or `"bot"` |
| `content` | Text | Message body |
| `timestamp` | DateTime | Auto-set on creation |

### `faqs`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `question` | String | Indexed for lookup |
| `answer` | Text | Returned on fuzzy match |

> **No migrations tool is configured.** Schema changes require manually dropping and recreating `chatbot.db`, then re-running `seed_faqs.py`.

---

## FAQ System

FAQ matching uses Python's `difflib.get_close_matches` against an **in-memory cache**.

- **Cache load:** on first request after startup (or after any FAQ write/delete)
- **Cache invalidation:** automatic on `POST /api/faqs/` and `DELETE /api/faqs/{id}`
- **Match cutoff:** `0.55` (lowered from original `0.70` to catch typos and short queries)
- **Match strategy:** case-insensitive comparison of the full question string
For large FAQ sets (500+), consider replacing `difflib` with a vector similarity search (e.g. sentence-transformers + FAISS).

---

## Rate Limiting

Implemented in `api/middleware/rate_limiter.py`.

- **Limit:** 20 messages per 60-second window per `session_id`
- **Storage:** in-memory `defaultdict` — **resets on server restart**
- **Response on breach:** HTTP `429 Too Many Requests`
For production, replace with a Redis-backed solution (e.g. `slowapi` with Redis store) to persist limits across restarts and multiple workers.

---

## Human Handoff

`handoff: true` is returned in the chat response when:

1. User message contains `"human"`, `"agent"`, or `"real person"`
2. `unknown_intent_count` reaches 3 consecutive turns
3. AI returns `intent: "human_agent_request"`
When `handoff: true`, the frontend should display an escalation UI and stop sending further messages to the bot. The actual routing to a human agent system (e.g. Zendesk, Intercom) must be implemented separately in the frontend or a downstream service.

---

## Known Limitations

| Issue | Detail |
|---|---|
| No DB migrations | Schema changes require manual DB reset |
| In-memory rate limiter | Resets on restart; not safe for multi-worker deployments |
| In-memory FAQ cache | Same reset caveat; also not shared across workers |
| No authentication | All endpoints are public; `session_id` is the only identity |
| SQLite | Not suitable for concurrent write-heavy production load; migrate to PostgreSQL for scale |
| `difflib` FAQ matching | String similarity only; no semantic understanding |
| NVIDIA NIM dependency | No local model fallback if NVIDIA API is down (falls to rule engine only) |
| `static/index.html` opened directly | Asset paths (`/static/css/...`, `/static/js/...`) and API calls are root-relative; only works when served by `main.py`, not via `file://` |