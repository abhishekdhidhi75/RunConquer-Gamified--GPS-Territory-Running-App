"""
Territories Router — Get user territories, nearby territories.
"""
import json
from fastapi import APIRouter, HTTPException, Depends, Query
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/mine")
async def get_my_territories(user=Depends(get_current_user)):
    """Get current user's territories."""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT t.id, t.polygon_json, t.area_sqm, t.color, t.created_at, t.last_defended,
                      u.username
               FROM territories t
               JOIN users u ON t.user_id = u.id
               WHERE t.user_id = ?
               ORDER BY t.created_at DESC""",
            (user["id"],)
        ).fetchall()

        territories = []
        for r in rows:
            territories.append({
                "id": r["id"],
                "polygon": json.loads(r["polygon_json"]),
                "area_sqm": r["area_sqm"],
                "color": r["color"],
                "username": r["username"],
                "created_at": r["created_at"],
                "last_defended": r["last_defended"]
            })
        return territories
    finally:
        conn.close()


@router.get("/all")
async def get_all_territories():
    """Get all territories (for map display)."""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT t.id, t.user_id, t.polygon_json, t.area_sqm, t.color, 
                      t.created_at, u.username, u.rank, u.level
               FROM territories t
               JOIN users u ON t.user_id = u.id
               ORDER BY t.area_sqm DESC
               LIMIT 200"""
        ).fetchall()

        territories = []
        for r in rows:
            territories.append({
                "id": r["id"],
                "user_id": r["user_id"],
                "polygon": json.loads(r["polygon_json"]),
                "area_sqm": r["area_sqm"],
                "color": r["color"],
                "username": r["username"],
                "rank": r["rank"],
                "level": r["level"],
                "created_at": r["created_at"]
            })
        return territories
    finally:
        conn.close()


@router.get("/user/{user_id}")
async def get_user_territories(user_id: int):
    """Get territories for a specific user."""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT t.id, t.polygon_json, t.area_sqm, t.color, t.created_at,
                      u.username
               FROM territories t
               JOIN users u ON t.user_id = u.id
               WHERE t.user_id = ?
               ORDER BY t.created_at DESC""",
            (user_id,)
        ).fetchall()

        return [{
            "id": r["id"],
            "polygon": json.loads(r["polygon_json"]),
            "area_sqm": r["area_sqm"],
            "color": r["color"],
            "username": r["username"],
            "created_at": r["created_at"]
        } for r in rows]
    finally:
        conn.close()
