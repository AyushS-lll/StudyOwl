#!/bin/bash
set -e

echo "=== StudyOwl: Setting up dev environment ==="

# ── Backend ──────────────────────────────────────
echo "Installing Python dependencies..."
cd /workspace/backend
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# ── Frontend ─────────────────────────────────────
echo "Installing Node dependencies..."
cd /workspace/frontend
npm install --silent

# ── Environment ──────────────────────────────────
if [ ! -f /workspace/.env ]; then
  echo "Creating .env from template..."
  cp /workspace/.env.example /workspace/.env
  echo "⚠️  Fill in your API keys in .env before running the app"
fi

# ── Database ─────────────────────────────────────
echo "Waiting for PostgreSQL..."
until pg_isready -h localhost -p 5432 -U studyowl 2>/dev/null; do
  sleep 1
done

echo "Running Alembic migrations..."
cd /workspace/backend
alembic upgrade head || echo "⚠️  Migrations failed — run manually: cd backend && alembic upgrade head"

echo ""
echo "✅ StudyOwl dev environment ready!"
echo ""
echo "Start backend:  cd backend && uvicorn main:app --reload --port 8000"
echo "Start frontend: cd frontend && npm run dev"
echo "API docs:       http://localhost:8000/docs"
