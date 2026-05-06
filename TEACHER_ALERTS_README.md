# StudyOwl — Teacher Alerts & Project Overview

## Project Summary
StudyOwl is an AI-powered homework assistant that guides students with graduated Socratic hints and surfaces teacher alerts when students struggle. The app is a monorepo with a Python FastAPI backend and a React + Vite frontend.

## Tech Stack
- Backend: Python 3.11, FastAPI, SQLAlchemy (async), Alembic (migrations)
- AI: Anthropic Claude (project uses `claude-sonnet-4-20250514` per design notes)
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS
- Database: PostgreSQL (development defaults to SQLite for local dev)
- Cache/session: Redis
- OCR: Tesseract via `pytesseract` + Pillow (Google Vision optional)
- Math verification: SymPy
- Alerts & Notifications: SendGrid (email) and Twilio (SMS) (configured via environment variables)
- Object storage: Cloudflare R2 (S3-compatible) for uploads
- Auth: JWT tokens (python-jose) + bcrypt

## Repository Layout (high level)
- `backend/` — FastAPI app and services
  - `backend/main.py` — app entry and CORS configuration
  - `backend/routers/` — API endpoints: `auth.py`, `sessions.py`, `alerts.py`, `progress.py`
  - `backend/services/` — domain services: `hint_engine.py`, `session_manager.py`, `answer_verifier.py`, `alert_service.py`, `ocr_service.py`
  - `backend/models/` — DB models: `student.py`, `session.py`, `attempt.py`
- `frontend/` — React app (Vite)
  - `frontend/src/api/studyowl.ts` — typed API client used across components
  - `frontend/src/pages/TeacherDash.tsx` — teacher dashboard UI

## Quick Setup (local dev)
1. Backend

   - Create and activate a Python virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

   - Configure environment variables: copy `.env.example` to `.env` and fill required keys (see *Environment* section).

   - Run migrations (if using Postgres) or let the app use local SQLite for quick dev.

   - Start the backend (development):

   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```

2. Frontend

   - Install packages and start dev server:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   - The Vite dev server proxies `/api` to the backend by default (see `frontend/vite.config.ts`).

3. Testing

   - Python tests (backend):

   ```bash
   cd backend
   pytest -q
   ```

   - Frontend testing: not included in the current repo; run the app and use the UI for manual verification.

## Environment Variables (important)
Edit `/workspaces/StudyOwl/.env` and set these at minimum for local dev:
- `DATABASE_URL` — e.g. `sqlite+aiosqlite:///studyowl.db` (dev) or a Postgres URL
- `SECRET_KEY` — JWT signing key (generate with `openssl rand -hex 32`)
- `REDIS_URL` — `redis://localhost:6379` (if running Redis)
- `SENDGRID_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` — for alerts (optional in dev)
- `R2_*` keys for uploads (optional)

## Auth Flow (high level)
- Frontend stores JWT in `localStorage` as `studyowl_token` after signup/login via `frontend/src/api/studyowl.ts`.
- `apiFetch()` attaches `Authorization: Bearer <token>` to all `/api` requests.
- Backend retrieves the header in `backend/routers/auth.py` dependency `get_current_student()`:
  - If header missing or malformed -> 401 `No token provided`.

Important: CORS must explicitly allow the `Authorization` header; otherwise browsers omit it during cross-origin requests. See `backend/main.py` for the CORS configuration.

## API Endpoints (key ones)
- `POST /api/auth/signup` — create user (student or teacher)
- `POST /api/auth/login` — login and return JWT
- `POST /api/session/start` — start a homework session (student)
- `POST /api/session/{id}/attempt` — submit an attempt for a session
- `GET /api/student/{id}/progress` — get student progress (teacher can view any student)
- `GET /api/student/list` — list all students (teacher only)
- `GET /api/alert` — get active alerts for teacher
- `GET /api/alert/metrics` — classroom metrics for teacher

Refer to router implementations in `backend/routers/` for request/response models.

## Alerts — Current Implementation Summary
Alerts are surfaced to teachers from `backend/routers/alerts.py` and triggered by `backend/services/session_manager.py` and `backend/services/alert_service.py`.

Current alert triggers (as designed in repo docs):
1. Student fails 3+ times at the same hint level
2. Student inactive for >10 minutes mid-session
3. Student sends a distress signal (detected by Claude classification)

What the alerts endpoints return:
- `GET /api/alert` returns sessions with `teacher_alerted == True` and `resolved == False` along with student name, question, hint level, and timestamps.
- `GET /api/alert/metrics` aggregates counts such as total students, sessions today, average success rate, and pending alert counts.

Database fields relevant to alerts (see `backend/models/session.py`):
- `hint_level` (int)
- `fails_at_level` (int)
- `teacher_alerted` (bool)
- `resolved` (bool)
- `started_at`, `resolved_at`

## Recommended Future Development Plan — Teacher Alerts (roadmap)
This section outlines short, medium, and long-term tasks to improve the alerts system and teacher UX.

Short-term (next 1–2 sprints):
- 1. Add severity levels to alerts
  - Add a `severity` enum column to `sessions` (e.g., `low`, `medium`, `high`)
  - Map triggers to severity (e.g., distress signal -> high)
  - Update `backend/routers/alerts.py` and `frontend/src/pages/TeacherDash.tsx` to display severity

- 2. Improve alert deduplication and coalescing
  - Ensure multiple failures across short time windows are grouped as a single active alert
  - Keep an alert history table for audit and teacher notes

- 3. Add teacher acknowledgement and resolution flow
  - `POST /api/alert/{id}/acknowledge` and `POST /api/alert/{id}/resolve`
  - Track `acknowledged_by`, `acknowledged_at`, `resolved_by`, `resolved_at`

Medium-term (2–4 sprints):
- 4. Real-time alerting
  - Add WebSocket / Server-Sent Events to push alerts to teachers immediately
  - Consider using a small pub/sub mechanism with Redis Streams or a message queue
  - Update `frontend` to subscribe to alert updates and show live badges

- 5. Multi-channel notifications
  - Implement SendGrid (email) and Twilio (SMS) notifications for `high` severity alerts
  - Add teacher preferences for notification channels and quiet hours

- 6. AI-based severity and clustering
  - Use Claude to classify the nature of the student's language (distress vs. confusion) and score severity
  - Cluster repeated failures across similar questions to detect conceptual gaps

Long-term (quarterly / product-level):
- 7. Teacher workflows and routing
  - Assign alerts to specific teachers or TAs
  - Escalation rules when alerts are unacknowledged
  - Integrate scheduling or office-hours assignment flows

- 8. Analytics and reporting
  - Aggregate alerts per class/student/teacher
  - Export reports and trends (CSV and dashboards)

## Implementation Notes & Where to Change Code
- To change alert triggers and logic: edit `backend/services/session_manager.py` and `backend/services/alert_service.py`.
- To change the alert data model: edit `backend/models/session.py` and create an Alembic migration in `backend/alembic/`.
- To update teacher UI: edit `frontend/src/pages/TeacherDash.tsx` and `frontend/src/api/studyowl.ts` (add endpoints for acknowledge/resolve).
- To add real-time push: consider `fastapi[websockets]` in backend and a small client in `frontend` that connects via `new WebSocket()` or SSE.

## Testing & Monitoring
- Unit tests: add `pytest` tests under `backend/tests/` for all alert triggers and API endpoints.
- Integration tests: use `httpx.AsyncClient` to simulate flows (student fails attempts -> alert triggered -> teacher sees alert).
- Logging & observability: add structured logs when alerts are triggered and when notifications are sent; integrate with Sentry or another APM.

## Security & Privacy Considerations
- Avoid storing sensitive student content in emails/SMS — only include minimal metadata and a secure link.
- Rate-limit automated notifications to prevent spam.
- Ensure audit trails for teacher actions (who acknowledged/resolved an alert).

## Next Steps (recommended immediate actions for your repo)
1. Add endpoints for alert acknowledgement and resolution and a small DB migration.
2. Add tests that simulate the three alert triggers described above.
3. Implement severity and teacher acknowledgement UI in `TeacherDash`.
4. Add basic WebSocket push for alerts (dev only) and plan for production message queue.

---

If you want, I can:
- Create the DB migration scaffold for the `severity` and `alert_history` changes.
- Implement the acknowledge/resolve endpoints and wire the frontend buttons in `TeacherDash.tsx`.
- Add unit tests for the alert triggers.

Tell me which of these you want me to implement next and I will proceed.
