# StudyOwl — Copilot Instructions

## Project overview
StudyOwl is an AI-powered homework assistant that guides students using Socratic questioning and graduated hints. It never gives direct answers. It escalates to a teacher only when a student is genuinely stuck.

Target users: K-12 and university students, their teachers, and school admins.

---

## Tech stack (strictly follow this)
| Layer | Technology |
|---|---|
| Backend | Python 3.11 + FastAPI + SQLAlchemy (async) + Alembic |
| AI | Anthropic Claude API (`claude-sonnet-4-20250514`) — `anthropic` SDK |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Charts | Recharts |
| Database | PostgreSQL 15 (SQLAlchemy async, `asyncpg` driver) |
| Cache / session state | Redis 7 |
| OCR | Tesseract (`pytesseract` + `Pillow`) for MVP; Google Vision API as upgrade |
| Math verification | SymPy |
| Alerts | SendGrid (email) + Twilio (SMS) |
| Object storage | Cloudflare R2 (boto3-compatible) — for photo uploads |
| Auth | JWT (python-jose) + bcrypt |
| Deployment | Railway (backend) + Railway (frontend static) + Railway Postgres + Railway Redis |
| Dev environment | GitHub Codespaces + Docker Compose |

---

## Monorepo structure
```
studyowl/
├── .devcontainer/devcontainer.json
├── .github/
│   ├── copilot-instructions.md    ← you are here
│   └── workflows/ci.yml
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── auth.py
│   ├── requirements.txt
│   ├── alembic/
│   ├── routers/
│   │   ├── sessions.py
│   │   ├── alerts.py
│   │   ├── progress.py
│   │   └── auth.py
│   ├── services/
│   │   ├── hint_engine.py
│   │   ├── subject_router.py
│   │   ├── answer_verifier.py
│   │   ├── ocr_service.py
│   │   ├── alert_service.py
│   │   └── session_manager.py
│   └── models/
│       ├── student.py
│       ├── session.py
│       └── attempt.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/studyowl.ts
│       ├── pages/
│       │   ├── StudentChat.tsx
│       │   └── TeacherDash.tsx
│       └── components/
│           ├── HintBubble.tsx
│           ├── PhotoUpload.tsx
│           └── ProgressChart.tsx
├── docker-compose.yml
├── railway.toml
└── .env.example
```

---

## Core domain logic — read this carefully

### The hint engine (backend/services/hint_engine.py)
- Always use the `anthropic` SDK, model `claude-sonnet-4-20250514`
- The system prompt must enforce the hint level and NEVER reveal the answer before level 3
- Level 1 = Socratic question only
- Level 2 = Point to the relevant formula or concept, no answer
- Level 3 = Near-answer with all values filled in; student completes the final step
- Every response MUST end with one short encouraging sentence
- Hints are stateless — full context (question, subject, previous attempts, level) is passed on every call

```python
HINT_SYSTEM = """
You are StudyOwl, a Socratic homework assistant. You NEVER give direct answers.
Hint level: {level}/3.
  Level 1 — Ask one Socratic question only. Do not explain or hint at the method.
  Level 2 — Point to the relevant formula or concept. Do not solve.
  Level 3 — Give a near-answer with all values substituted. Student must perform the final calculation.
Subject area: {subject}
Always end with exactly one short encouraging sentence.
"""
```

### Session state machine (backend/services/session_manager.py)
```
START
  └─ hint_level = 1, fails_at_level = 0
       │
  student submits attempt
       │
  ┌────▼──────────────┐
  │  answer_verifier  │
  └────┬──────────────┘
       │
  ┌────▼──── correct? ────▶ log success ──▶ END
  │
  wrong
  │
  fails_at_level += 1
  │
  ├── fails_at_level >= 3? ──▶ trigger teacher alert
  │
  ├── hint_level < 3? ──▶ advance hint_level, reset fails_at_level
  │
  └── get_hint(question, subject, hint_level, attempts)
```

### Teacher alert triggers (ANY of these fires an alert)
1. Student fails 3+ times at the same hint level
2. Student inactive for >10 minutes mid-session
3. Student sends a distress signal (detected by Claude: "I don't understand anything", "I give up", etc.)

### Subject classification
Use Claude to classify incoming questions into: `math`, `science`, `english`, `history`, `other`.
Pass the subject to the hint engine and answer verifier.
For `math`, use SymPy for answer verification. For others, use Claude to judge correctness.

---

## Database schema

```sql
-- students
id UUID PK, name TEXT, email TEXT UNIQUE, grade_level TEXT,
role TEXT DEFAULT 'student', -- 'student' | 'teacher' | 'admin'
hashed_password TEXT, created_at TIMESTAMP

-- sessions
id UUID PK, student_id UUID FK→students,
question TEXT, subject TEXT,
hint_level INT DEFAULT 1, fails_at_level INT DEFAULT 0,
resolved BOOLEAN DEFAULT FALSE,
teacher_alerted BOOLEAN DEFAULT FALSE,
photo_url TEXT, -- S3/R2 URL if uploaded
started_at TIMESTAMP, resolved_at TIMESTAMP

-- attempts
id UUID PK, session_id UUID FK→sessions,
attempt_text TEXT, is_correct BOOLEAN,
hint_shown TEXT, hint_level INT,
created_at TIMESTAMP
```

---

## API contract

### POST /api/session/start
Request: `{ student_id, question, photo_b64? }`
Response: `{ session_id, hint, hint_level: 1, subject }`

### POST /api/session/{id}/attempt
Request: `{ attempt_text }`
Response: `{ status: "correct"|"wrong", hint?, hint_level?, message }`

### GET /api/student/{id}/progress
Response: `{ subjects: [{name, sessions, success_rate}], recent_sessions: [...] }`

### POST /api/alert (internal, called by session manager)
Sends teacher alert via SendGrid.

---

## Environment variables (.env)
```
ANTHROPIC_API_KEY=
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/studyowl
REDIS_URL=redis://localhost:6379
SENDGRID_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
GOOGLE_VISION_API_KEY=          # optional, Tesseract used by default
R2_ACCESS_KEY=
R2_SECRET_KEY=
R2_BUCKET=
R2_ENDPOINT=
SECRET_KEY=                     # JWT signing key (generate with: openssl rand -hex 32)
```

---

## Code style rules (enforce these in every file)
- Python: type hints on every function signature. Use `async def` for all DB and external API calls. Pydantic v2 models for all request/response schemas.
- TypeScript: strict mode. No `any`. Use `interface` for API response shapes.
- No direct answer strings in API responses unless `hint_level == 3` and answer is exhausted.
- Every service function must have a docstring explaining what it does and what it returns.
- Tests go in `backend/tests/` using `pytest` + `httpx.AsyncClient`.

---

## What Copilot should NOT do
- Never generate code that directly returns the answer to a homework question without going through the hint engine
- Never skip the session state machine — every student interaction must pass through `session_manager.process_attempt()`
- Never hardcode API keys
- Never use `requests` (sync) — always use `httpx` (async) for outbound HTTP calls
- Never use `float` for financial or grade data — use `Decimal`
