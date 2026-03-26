# StudyOwl — GitHub Copilot Build Guide

A step-by-step process for building StudyOwl using GitHub Copilot in Codespaces.
Follow these steps in order. Each step tells you exactly what to ask Copilot.

---

## Phase 0 — Repo setup (do this once, locally or in browser)

1. Create a new GitHub repository named `studyowl` (private)
2. Copy all files from this blueprint into the root of that repo
3. Commit and push everything:
   ```bash
   git add .
   git commit -m "chore: initial StudyOwl scaffold"
   git push
   ```
4. In the repo, click **Code → Codespaces → Create codespace on main**
5. Wait ~3 minutes for the devcontainer to build and `setup.sh` to run
6. You now have: FastAPI + React + Postgres + Redis + Copilot all wired up

---

## Phase 1 — Backend core (Week 1)

Work in the `backend/` folder. Open **Copilot Chat** (`Ctrl+Shift+I`) for each task.

### Step 1.1 — Database models
Open `backend/models/` and say to Copilot Chat:

> "Using SQLAlchemy 2.0 async with the schema in `.github/copilot-instructions.md`, generate the Student, Session, and Attempt models. Include `__tablename__`, all columns, relationships, and `__repr__`. Use `uuid.uuid4` as default PKs."

Review the output. Then ask:

> "Now generate the Alembic migration for these three models."

Run it:
```bash
cd backend && alembic upgrade head
```

---

### Step 1.2 — Hint engine
Open `backend/services/hint_engine.py` (already scaffolded). Say to Copilot Chat:

> "The skeleton is in hint_engine.py. Add error handling: catch `anthropic.APIError` and `anthropic.RateLimitError`, log them, and raise a friendly `HTTPException(503)`. Also add a unit test in `backend/tests/test_hint_engine.py` that mocks the Anthropic client."

---

### Step 1.3 — Subject router
Open `backend/services/subject_router.py` (empty). Say to Copilot Chat:

> "Create `subject_router.py` following the pattern in hint_engine.py. Call Claude to classify a question into one of: math, science, english, history, other. Return the classification as a lowercase string. Use a single-sentence system prompt and `max_tokens=10`. Handle API errors gracefully."

---

### Step 1.4 — Answer verifier
Open `backend/services/answer_verifier.py` (empty). Say to Copilot Chat:

> "Create `answer_verifier.py`. For subject='math', use SymPy to parse and compare the student's answer to the correct answer (extract it from the question using Claude first). For all other subjects, call Claude with a strict yes/no system prompt to judge if the attempt is correct. Signature: `async def check(question: str, answer: str, subject: str) -> bool`"

---

### Step 1.5 — Session router (API endpoints)
Open `backend/routers/sessions.py` (empty). Say to Copilot Chat:

> "Create the FastAPI router for sessions. Two endpoints following the API contract in copilot-instructions.md: POST /start and POST /{session_id}/attempt. Use the session_manager service. Add Pydantic v2 request/response models at the top of the file. Inject AsyncSession via FastAPI Depends."

Test it:
```bash
curl -X POST http://localhost:8000/api/session/start \
  -H "Content-Type: application/json" \
  -d '{"student_id": "00000000-0000-0000-0000-000000000001", "question": "What is 12 × 7?"}'
```

---

### Step 1.6 — OCR service
Open `backend/services/ocr_service.py` (empty). Say to Copilot Chat:

> "Create `ocr_service.py`. Implement `extract_text(image_b64: str) -> str` using pytesseract. Add a second implementation `extract_text_google(image_b64: str) -> str` using the Google Vision API (only called if GOOGLE_VISION_API_KEY is set in config). The public function should automatically pick the right backend."

---

### Step 1.7 — Alert service
Open `backend/services/alert_service.py` (empty). Say to Copilot Chat:

> "Create `alert_service.py`. Implement `async def notify_teacher(session, reason: str)`. Send an email via SendGrid with the alert payload defined in copilot-instructions.md. Format it as a clean HTML email. If SENDGRID_API_KEY is empty, log the alert to console instead (for local dev)."

---

### Step 1.8 — Auth
Open `backend/routers/auth.py` and say:

> "Create JWT auth for StudyOwl. POST /token (OAuth2 form, returns access_token), POST /register (creates student/teacher), GET /me (returns current user). Use python-jose for JWT, passlib/bcrypt for passwords. Follow the config in config.py for SECRET_KEY and algorithm."

---

### Step 1.9 — Progress router
Open `backend/routers/progress.py` and say:

> "Create GET /api/student/{student_id}/progress. Query the attempts table to calculate per-subject success rates and return the last 10 sessions. Use the StudentProgress response shape from the frontend's studyowl.ts type definitions."

---

## Phase 2 — Frontend (Week 2)

Work in `frontend/src/`. Keep `backend` running in one terminal.

### Step 2.1 — App shell + routing
Open `frontend/src/App.tsx` and say to Copilot Chat:

> "Set up React Router v6 in App.tsx with two routes: /chat → StudentChat, /dashboard → TeacherDash. Add a simple nav bar with the StudyOwl owl emoji logo. Use Tailwind for styling. No auth guard yet."

---

### Step 2.2 — Student chat UI
Open `frontend/src/pages/StudentChat.tsx` and say:

> "Build the StudentChat page. It should: (1) show a text area for the student to type a question, (2) on submit call api.startSession(), (3) display the returned hint in a HintBubble component, (4) show an input for the student's answer attempt, (5) on submit call api.submitAttempt(), (6) update the hint bubble with each response. Use Tailwind. Show the hint level (1/2/3) as a small badge on the bubble. Show a green success banner when status is 'correct'."

---

### Step 2.3 — Hint bubble component
Open `frontend/src/components/HintBubble.tsx` and say:

> "Create HintBubble. Props: hint (string), level (1|2|3), isLoading (boolean). Level 1 = blue border, Level 2 = amber border, Level 3 = orange border. Show a pulsing skeleton when isLoading is true. Add a small owl emoji icon on the left. Keep it friendly and readable."

---

### Step 2.4 — Photo upload component
Open `frontend/src/components/PhotoUpload.tsx` and say:

> "Create PhotoUpload. It should accept drag-and-drop OR a file picker. When a file is selected, read it as base64 and call the onUpload(b64: string) callback prop. Show a preview thumbnail of the selected image. Add a 'Take photo' button that triggers the camera on mobile (use `capture='environment'` on the input). Style with Tailwind."

---

### Step 2.5 — Teacher dashboard
Open `frontend/src/pages/TeacherDash.tsx` and say:

> "Build the teacher dashboard. Fetch api.getProgress(studentId) on mount. Show: (1) a Recharts BarChart of success rate per subject, (2) a table of recent sessions with columns: question preview, subject, attempts, resolved status, date. Use Tailwind for layout. Add a simple student ID selector at the top."

---

### Step 2.6 — Progress chart component
Open `frontend/src/components/ProgressChart.tsx` and say:

> "Create ProgressChart. Props: subjects (SubjectProgress[]). Render a Recharts ResponsiveContainer BarChart. X-axis = subject name, Y-axis = success_rate as a percentage. Colour bars: green if rate > 70%, amber if 40-70%, red if below 40%. Add a tooltip showing exact rate and session count."

---

## Phase 3 — Polish + deploy (Week 3)

### Step 3.1 — Auth integration
Say to Copilot Chat:

> "Add a login page to the frontend that calls api.login(). Add an auth guard: redirect unauthenticated users to /login. Decode the JWT from localStorage to get student_id for API calls. Add a logout button to the nav."

### Step 3.2 — Inactivity detection
Say to Copilot Chat:

> "In the session_manager, add a background task that checks if a session has had no activity for more than `settings.inactivity_timeout_minutes` minutes. If so, call `_trigger_alert` with reason 'Inactivity timeout'. Use FastAPI's BackgroundTasks or a Redis-based expiry key."

### Step 3.3 — Deploy to Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
railway init

# Add Postgres and Redis plugins in the Railway dashboard

# Deploy
railway up
```

Then set all env vars from `.env.example` in the Railway dashboard under Variables.

---

## Copilot tips for this project

| Situation | What to say |
|---|---|
| Copilot gives you sync code | "Rewrite this to be fully async using `async def` and `await`" |
| Copilot skips type hints | "Add full Python type hints to every function signature" |
| Copilot writes a direct answer | "This violates the StudyOwl guardrail. Rewrite so it only returns a hint, never the answer" |
| You want tests | "Write pytest tests for this function. Mock external API calls with `unittest.mock.patch`" |
| Something is unclear | Open the file + say "Explain what this function does and how it fits into the StudyOwl session state machine" |

---

## Useful commands cheatsheet

```bash
# Backend
cd backend
uvicorn main:app --reload --port 8000   # start with hot reload
alembic revision --autogenerate -m "msg" # create migration
alembic upgrade head                     # apply migrations
pytest tests/ -v                         # run tests

# Frontend
cd frontend
npm run dev          # start Vite dev server
npm run build        # production build

# Docker
docker-compose up -d postgres redis      # start just the data services
docker-compose logs -f backend           # tail backend logs
```
