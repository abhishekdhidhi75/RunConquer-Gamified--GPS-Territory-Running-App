"""
Authentication Router — Register, Login, JWT tokens.
"""
import hashlib
import secrets
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import get_db

router = APIRouter()


def hash_password(password: str) -> str:
    """Hash password with SHA-256 + random salt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt, hashed = stored_hash.split("$", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == hashed
    except ValueError:
        return False
security = HTTPBearer()

SECRET_KEY = "runconquer-secret-key-change-in-production-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 72


# --- Pydantic Models ---

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# --- Helpers ---

def create_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
        username = payload["username"]
        return {"id": user_id, "username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# --- Endpoints ---

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    if len(req.username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    conn = get_db()
    try:
        # Check if username or email exists
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (req.username, req.email)
        ).fetchone()
        if existing:
            raise HTTPException(400, "Username or email already registered")

        # Create user
        hashed = hash_password(req.password)
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (req.username, req.email, hashed)
        )
        conn.commit()
        user_id = cursor.lastrowid

        token = create_token(user_id, req.username)
        return TokenResponse(
            access_token=token,
            user={"id": user_id, "username": req.username, "email": req.email}
        )
    finally:
        conn.close()


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (req.username,)
        ).fetchone()
        if not row or not verify_password(req.password, row["password_hash"]):
            raise HTTPException(401, "Invalid username or password")

        token = create_token(row["id"], row["username"])
        return TokenResponse(
            access_token=token,
            user={
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "total_xp": row["total_xp"],
                "level": row["level"],
                "rank": row["rank"],
            }
        )
    finally:
        conn.close()


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "total_xp": row["total_xp"],
            "level": row["level"],
            "rank": row["rank"],
            "total_area_sqm": row["total_area_sqm"],
            "total_distance_km": row["total_distance_km"],
            "total_runs": row["total_runs"],
            "streak_days": row["streak_days"],
            "avatar_color": row["avatar_color"],
            "created_at": row["created_at"],
        }
    finally:
        conn.close()
