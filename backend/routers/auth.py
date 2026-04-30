"""
Authentication router — sign up, login, token refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from datetime import timedelta
import bcrypt
from jose import JWTError, jwt

from db import get_db
from config import settings
from models.student import Student
from sqlalchemy import select

router = APIRouter()


# ── Request/Response Models ────────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    name: str
    email: EmailStr
    password: str  # Will be truncated to 72 bytes due to bcrypt limit
    grade_level: str
    role: str = "student"  # "student" | "teacher"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Helpers ────────────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt. Truncate to 72 bytes due to bcrypt limitation."""
    # bcrypt can only hash passwords up to 72 bytes
    truncated = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(truncated.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash. Truncate to 72 bytes due to bcrypt limit."""
    truncated = plaintext.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    try:
        return bcrypt.checkpw(truncated.encode('utf-8'), hashed.encode('utf-8'))
    except (ValueError, TypeError):
        return False


def create_access_token(email: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode = {"sub": email}
    encode_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encode_jwt


async def get_current_student(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Student:
    """
    Dependency: validates JWT token and returns the current student.
    Extracts token from Authorization header: "Bearer <token>".
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    stmt = select(Student).where(Student.email == email)
    result = await db.execute(stmt)
    student = result.scalars().first()
    
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return student


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.post("/signup", response_model=TokenResponse)
async def signup(req: SignUpRequest, db: AsyncSession = Depends(get_db)):
    """Create a new student or teacher account."""
    # Check if email already exists
    stmt = select(Student).where(Student.email == req.email)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new student
    student = Student(
        name=req.name,
        email=req.email,
        hashed_password=hash_password(req.password),
        grade_level=req.grade_level,
        role=req.role,
    )
    db.add(student)
    await db.commit()
    
    # Return token
    access_token = create_access_token(email=req.email)
    return {"access_token": access_token}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Log in an existing student or teacher."""
    stmt = select(Student).where(Student.email == req.email)
    result = await db.execute(stmt)
    student = result.scalars().first()
    
    if not student or not verify_password(req.password, student.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(email=req.email)
    return {"access_token": access_token}
