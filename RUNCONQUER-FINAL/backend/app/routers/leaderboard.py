"""
Leaderboard Router — Global rankings and stats.
"""
from fastapi import APIRouter, Depends
from app.database import get_db
from app.routers.auth import get_current_user
from app.services.game_service import get_user_achievements, get_rank_icon

router = APIRouter()


@router.get("/global")
async def get_global_leaderboard():
    """Get global leaderboard ranked by total area conquered."""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT id, username, total_xp, level, rank, 
                      total_area_sqm, total_distance_km, total_runs,
                      streak_days, avatar_color
               FROM users 
               ORDER BY total_area_sqm DESC
               LIMIT 100"""
        ).fetchall()

        leaderboard = []
        for i, r in enumerate(rows, 1):
            leaderboard.append({
                "position": i,
                "user_id": r["id"],
                "username": r["username"],
                "total_xp": r["total_xp"],
                "level": r["level"],
                "rank": r["rank"],
                "rank_icon": get_rank_icon(r["rank"]),
                "total_area_sqm": r["total_area_sqm"],
                "total_area_display": format_area(r["total_area_sqm"]),
                "total_distance_km": round(r["total_distance_km"], 1),
                "total_runs": r["total_runs"],
                "streak_days": r["streak_days"],
                "avatar_color": r["avatar_color"]
            })
        return leaderboard
    finally:
        conn.close()


@router.get("/stats")
async def get_my_stats(user=Depends(get_current_user)):
    """Get current user's full stats."""
    conn = get_db()
    try:
        user_row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user["id"],)
        ).fetchone()
        if not user_row:
            return {}

        # Get rank position
        rank_pos = conn.execute(
            "SELECT COUNT(*) as pos FROM users WHERE total_area_sqm > ?",
            (user_row["total_area_sqm"],)
        ).fetchone()["pos"] + 1

        # Get total players
        total_players = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]

        # Get achievements
        achievements = get_user_achievements(user["id"])

        # Get recent runs
        recent_runs = conn.execute(
            """SELECT id, distance_km, duration_seconds, avg_speed_kmh, xp_earned, area_sqm, created_at
               FROM runs WHERE user_id = ? AND is_valid = 1
               ORDER BY created_at DESC LIMIT 5""",
            (user["id"],)
        ).fetchall()

        return {
            "user": {
                "id": user_row["id"],
                "username": user_row["username"],
                "total_xp": user_row["total_xp"],
                "level": user_row["level"],
                "rank": user_row["rank"],
                "rank_icon": get_rank_icon(user_row["rank"]),
                "total_area_sqm": user_row["total_area_sqm"],
                "total_area_display": format_area(user_row["total_area_sqm"]),
                "total_distance_km": round(user_row["total_distance_km"], 1),
                "total_runs": user_row["total_runs"],
                "streak_days": user_row["streak_days"],
                "avatar_color": user_row["avatar_color"],
                "created_at": user_row["created_at"],
            },
            "ranking": {
                "position": rank_pos,
                "total_players": total_players,
                "percentile": round(((total_players - rank_pos) / max(1, total_players)) * 100, 1)
            },
            "achievements": achievements,
            "recent_runs": [dict(r) for r in recent_runs]
        }
    finally:
        conn.close()


def format_area(area_sqm: float) -> str:
    """Format area for display."""
    if area_sqm >= 1_000_000:
        return f"{area_sqm / 1_000_000:.2f} km²"
    elif area_sqm >= 10_000:
        return f"{area_sqm / 10_000:.2f} ha"
    else:
        return f"{area_sqm:,.0f} m²"
