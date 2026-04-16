# StudyOwl — Local Development Setup Guide

## ✅ Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Git

---

## 🚀 Quick Start

### 1. **Clone and Navigate**
```bash
cd /workspaces/StudyOwl
```

### 2. **Set up Environment**
```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API keys:
# - ANTHROPIC_API_KEY=sk-ant-...
# - SENDGRID_API_KEY= (optional for dev)
# - TWILIO_ACCOUNT_SID= (optional for dev)
# - SECRET_KEY=<generate with: openssl rand -hex 32>
```

### 3. **Start Docker Compose (Database + Redis)**
```bash
docker-compose up -d
```
This starts:
- PostgreSQL 15 on `localhost:5432`
- Redis 7 on `localhost:6379`

Verify:
```bash
docker-compose ps
```

### 4. **Backend Setup**
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server runs on: **http://localhost:8000**
- API docs: http://localhost:8000/docs (Swagger UI)
- Health check: http://localhost:8000/health

### 5. **Frontend Setup** (in a new terminal)
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

Frontend runs on: **http://localhost:5173**

---

## 📝 First-Time Database Setup

The database tables are created automatically on first API start via the `init_db()` lifespan event in `main.py`.

To manually verify schema:
```bash
# Connect to PostgreSQL
psql postgresql://studyowl:studyowl@localhost/studyowl

# List tables
\dt

# Quit
\q
```

Expected tables: `students`, `sessions`, `attempts`

---

## 🧪 Testing the Full Workflow

### 1. **Sign Up** (Frontend)
Navigate to http://localhost:5173
- Click "Sign up"
- Create a student account
- You'll be logged in and see the StudentChat interface

### 2. **Ask a Question**
- Paste a homework question (e.g., "What is 2 + 2?")
- Click "Get First Hint"
- You should see a Level 1 (Socratic) hint

### 3. **Submit Answers**
- Type an answer and press "Submit Answer"
- Correct: Session closes with celebration message
- Wrong: Get a Level 2 hint, answer again

### 4. **Teacher Dashboard** (Optional)
- Sign up as a teacher with role=`teacher`
- After 3 failed attempts, you'll see alerts

---

## 🐛 Common Issues

### **Postgres Connection Error**
```
FATAL: role "studyowl" does not exist
```
**Solution:** Docker Compose auto-creates this; if missing, restart:
```bash
docker-compose down
docker-compose up -d
```

### **Port Already in Use**
- Backend conflicts on 8000? Change `uvicorn ... --port 9000`
- Frontend conflicts on 5173? Vite auto-increments (5174, etc.)

### **Missing API Key Errors**
The app won't start without:
- `ANTHROPIC_API_KEY` (required)
- `SECRET_KEY` (random for JWT signing)

Others (`SENDGRID_API_KEY`, etc.) are optional for MVP.

### **CORS Errors in Frontend**
Check `config.py` `allowed_origins`:
```python
allowed_origins: list[str] = ["http://localhost:5173"]
```
Frontend must match exactly.

---

## 📦 Project Structure

```
backend/
├── main.py                  # FastAPI app, router registration
├── config.py               # Pydantic settings
├── db.py                   # SQLAlchemy setup
├── models/
│   ├── student.py
│   ├── session.py
│   ├── attempt.py
│   └── __init__.py
├── services/
│   ├── hint_engine.py      # Claude API → hints
│   ├── session_manager.py  # State machine
│   ├── answer_verifier.py  # Math/general verification
│   ├── alert_service.py    # SendGrid/Twilio
│   ├── subject_router.py   # Question classification
│   ├── ocr_service.py      # Tesseract/Google Vision
│   └── __init__.py
├── routers/
│   ├── auth.py            # /api/auth/signup, /api/auth/login
│   ├── sessions.py        # /api/session/start, /api/session/{id}/attempt
│   ├── progress.py        # /api/student/{id}/progress
│   ├── alerts.py          # /api/alert/ (teacher only)
│   └── __init__.py
└── requirements.txt

frontend/
├── src/
│   ├── main.tsx           # React entry point
│   ├── App.tsx            # Auth + routing
│   ├── index.css          # Tailwind styles
│   ├── api/
│   │   └── studyowl.ts    # Typed API client
│   ├── pages/
│   │   ├── StudentChat.tsx  # Main student interface
│   │   └── TeacherDash.tsx  # Teacher alerts/analytics
│   └── components/
│       ├── HintBubble.tsx
│       ├── PhotoUpload.tsx
│       └── ProgressChart.tsx
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── tsconfig.json
└── package.json
```

---

## 🔧 Development Workflows

### **Running Tests**
```bash
cd backend
pytest
```

### **Linting**
```bash
# Python (backend)
cd backend && ruff check .

# TypeScript (frontend)
cd frontend && npm run lint
```

### **Database Migrations** (Future)
When you modify models, use Alembic:
```bash
cd backend
alembic revision --autogenerate -m "Add column foo"
alembic upgrade head
```

### **Resetting Database**
```bash
docker-compose down  # Stops and removes containers (data deleted)
docker-compose up -d  # Fresh start
# Re-run backend to create tables
```

---

## 📚 Tech Docs

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Anthropic Claude API**: https://docs.anthropic.com/
- **React 18**: https://react.dev/
- **Tailwind CSS**: https://tailwindcss.com/

---

## 🚢 Deployment (Railway)

See `railway.toml` — configured for:
- Backend: Python 3.11 + FastAPI
- Frontend: Node.js + Vite static build
- Postgres plugin
- Redis plugin

Deploy with:
```bash
railway up
```

---

## 📞 Support

For issues, check:
1. `.github/copilot-instructions.md` — Project spec
2. `COPILOT_BUILD_GUIDE.md` — Build notes
3. Logs: `docker-compose logs -f`

---

**Happy coding! 🦉**
