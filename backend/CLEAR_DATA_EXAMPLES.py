"""
Quick one-liner scripts to clear StudentOwl data.
Copy and run these from the backend directory.
"""

# ============================================================================
# OPTION 1: Using the clear_all_data.py script (Recommended)
# ============================================================================

"""
cd /workspaces/StudyOwl/backend
source /workspaces/StudyOwl/.venv/bin/activate

# Show statistics
python clear_all_data.py stats

# Clear all students (cascade deletes sessions/attempts)
python clear_all_data.py students

# Clear all sessions only
python clear_all_data.py sessions

# Clear all attempts only
python clear_all_data.py attempts

# Clear all student data + Redis cache
python clear_all_data.py all

# Full database reset (drop all tables and recreate)
python clear_all_data.py reset

# Clear Redis only
python clear_all_data.py redis
"""


# ============================================================================
# OPTION 2: Quick inline Python (if you want one-liner)
# ============================================================================

"""
python3 << 'EOF'
import asyncio
from sqlalchemy import delete
from db import SessionLocal
from models.student import Student

async def clear_students():
    async with SessionLocal() as db:
        result = await db.execute(delete(Student))
        await db.commit()
        print(f"✅ Deleted {result.rowcount} students (and their sessions/attempts via cascade)")

asyncio.run(clear_students())
EOF
"""


# ============================================================================
# OPTION 3: Using FastAPI route (call from frontend)
# ============================================================================

"""
# Add this to backend/routers/auth.py or create a new admin.py:

@router.post("/admin/clear-all-students")
async def clear_all_students(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    '''Only accessible by admin.'''
    if student.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    from sqlalchemy import delete
    
    result = await db.execute(delete(Student))
    await db.commit()
    
    return {
        "status": "success",
        "deleted_students": result.rowcount,
        "message": f"Deleted {result.rowcount} students and all their sessions/attempts"
    }

# Then call from frontend:
# POST http://localhost:8000/api/auth/admin/clear-all-students
# with Authorization header
"""


# ============================================================================
# OPTION 4: Direct database SQL (if you prefer raw SQL)
# ============================================================================

"""
# Connect to PostgreSQL directly:
psql postgresql://user:password@localhost/studyowl

# Then run:
DELETE FROM attempts;                 -- Delete all attempts first (cascade)
DELETE FROM sessions;                 -- Delete all sessions
DELETE FROM students;                 -- Delete all students

-- Or all at once with cascade:
TRUNCATE TABLE students CASCADE;

-- Verify:
SELECT COUNT(*) FROM students;
SELECT COUNT(*) FROM sessions;
SELECT COUNT(*) FROM attempts;
"""


# ============================================================================
# OPTION 5: Clear Redis directly
# ============================================================================

"""
# Connect to Redis:
redis-cli

# Then run:
> FLUSHALL              # Clear everything
> KEYS *                # Verify (should be empty)

# Or from command line:
redis-cli FLUSHALL
"""
