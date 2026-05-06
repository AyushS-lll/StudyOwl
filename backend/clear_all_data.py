"""
Clear all students and session data from StudyOwl.

This script provides multiple options:
- Clear all students (and cascade-deletes sessions/attempts)
- Clear all sessions
- Clear all attempts
- Clear Redis cache
- Full reset (everything)
"""

import asyncio
import sys
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from db import engine, SessionLocal, Base
from models.student import Student
from models.session import Session
from models.attempt import Attempt
from config import settings


async def clear_students(db: AsyncSession) -> int:
    """Delete all students (cascade deletes sessions and attempts)."""
    result = await db.execute(delete(Student))
    await db.commit()
    count = result.rowcount
    print(f"✅ Deleted {count} students")
    return count


async def clear_sessions(db: AsyncSession) -> int:
    """Delete all sessions (cascade deletes attempts)."""
    result = await db.execute(delete(Session))
    await db.commit()
    count = result.rowcount
    print(f"✅ Deleted {count} sessions")
    return count


async def clear_attempts(db: AsyncSession) -> int:
    """Delete all attempts."""
    result = await db.execute(delete(Attempt))
    await db.commit()
    count = result.rowcount
    print(f"✅ Deleted {count} attempts")
    return count


async def clear_redis() -> None:
    """Clear all Redis cache."""
    try:
        import redis.asyncio as redis
        
        # Parse Redis URL
        r = await redis.from_url(settings.redis_url, decode_responses=True)
        await r.flushall()
        await r.close()
        print(f"✅ Redis cache cleared")
    except Exception as e:
        print(f"⚠️  Could not clear Redis: {e}")


async def reset_database() -> None:
    """Drop all tables and recreate them."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("✅ Dropped all tables")
        
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Recreated all tables")


async def full_reset() -> None:
    """Complete reset: drop DB tables, recreate them, clear Redis."""
    print("\n🔄 Starting full reset...\n")
    
    # Reset database
    await reset_database()
    
    # Clear Redis
    await clear_redis()
    
    print("\n✅ Full reset complete!")


async def clear_all_student_data() -> None:
    """Clear all students, sessions, and attempts (preserves DB schema)."""
    print("\n🔄 Clearing all student data...\n")
    
    async with SessionLocal() as db:
        # Delete students (cascade will delete sessions and attempts)
        await clear_students(db)
        await clear_attempts(db)
        await clear_sessions(db)
    
    # Clear Redis
    await clear_redis()
    
    print("\n✅ All student data cleared!")


async def show_stats() -> None:
    """Show current data statistics."""
    async with SessionLocal() as db:
        from sqlalchemy import func
        
        student_count = (await db.execute(delete(Student.__table__).returning(Student.id))).rowcount if False else 0
        
        # Get counts without deleting
        from sqlalchemy import select
        students = await db.execute(select(func.count(Student.id)))
        sessions = await db.execute(select(func.count(Session.id)))
        attempts = await db.execute(select(func.count(Attempt.id)))
        
        print(f"""
📊 Current Statistics:
  • Students: {students.scalar() or 0}
  • Sessions: {sessions.scalar() or 0}
  • Attempts: {attempts.scalar() or 0}
        """)


async def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("""
📚 StudyOwl Data Management Tool

Usage: python clear_all_data.py [COMMAND]

Commands:
  students        Delete all students (cascade deletes sessions/attempts)
  sessions        Delete all sessions (keeps students)
  attempts        Delete all attempts
  redis           Clear Redis cache only
  all             Clear students, sessions, attempts, and Redis
  reset           Full database reset (drop and recreate all tables)
  stats           Show current data statistics

Examples:
  python clear_all_data.py students
  python clear_all_data.py all
  python clear_all_data.py reset
        """)
        return
    
    command = sys.argv[1].lower()
    
    async with SessionLocal() as db:
        if command == "students":
            await clear_students(db)
        elif command == "sessions":
            await clear_sessions(db)
        elif command == "attempts":
            await clear_attempts(db)
        elif command == "redis":
            await clear_redis()
        elif command == "all":
            await clear_all_student_data()
        elif command == "reset":
            await full_reset()
        elif command == "stats":
            await show_stats()
        else:
            print(f"❌ Unknown command: {command}")
            print("Use: python clear_all_data.py [students|sessions|attempts|redis|all|reset|stats]")


if __name__ == "__main__":
    asyncio.run(main())
