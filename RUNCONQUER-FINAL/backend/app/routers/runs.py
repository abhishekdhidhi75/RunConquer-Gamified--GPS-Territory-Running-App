"""
Runs Router — Submit runs, get run history, run analysis.
"""
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.routers.auth import get_current_user
from app.services.geo_service import total_path_distance, path_to_territory, shoelace_area
from app.services.game_service import (
    calculate_xp_for_run, calculate_level, get_rank,
    update_streak, check_and_award_achievements
)
from app.services.ml_service import extract_features, calculate_cheat_score, is_run_valid, get_cheat_analysis

router = APIRouter()


class PointModel(BaseModel):
    lat: float
    lng: float


class SubmitRunRequest(BaseModel):
    path: List[PointModel]
    start_time: str
    end_time: str
    duration_seconds: int


@router.post("/submit")
async def submit_run(req: SubmitRunRequest, user=Depends(get_current_user)):
    """Submit a completed run with GPS path."""
    if len(req.path) < 4:
        raise HTTPException(400, "Run path must have at least 4 points")

    path_points = [(p.lat, p.lng) for p in req.path]

    # Calculate distance
    distance_km = total_path_distance(path_points)
    if distance_km < 0.01:
        raise HTTPException(400, "Run is too short")

    # Calculate speed
    avg_speed = (distance_km / (req.duration_seconds / 3600.0)) if req.duration_seconds > 0 else 0

    # ML Cheat Detection
    features = extract_features(path_points, req.duration_seconds)
    cheat_score = calculate_cheat_score(features) if features else 0.0
    valid = is_run_valid(cheat_score)

    # Territory calculation
    territory_result = path_to_territory(path_points)
    area_sqm = territory_result["area_sqm"] if territory_result else 0.0
    territory_polygon = territory_result["polygon"] if territory_result else None
    new_territory = territory_result is not None and valid

    conn = get_db()
    try:
        # Save run
        path_json = json.dumps([{"lat": p.lat, "lng": p.lng} for p in req.path])
        territory_json = json.dumps(
            [{"lat": p[0], "lng": p[1]} for p in territory_polygon]
        ) if territory_polygon else None

        cursor = conn.execute(
            """INSERT INTO runs 
            (user_id, start_time, end_time, duration_seconds, distance_km, 
             avg_speed_kmh, path_json, territory_polygon_json, area_sqm,
             cheat_score, is_valid, xp_earned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user["id"], req.start_time, req.end_time, req.duration_seconds,
                round(distance_km, 3), round(avg_speed, 2),
                path_json, territory_json, round(area_sqm, 2),
                cheat_score, 1 if valid else 0, 0
            )
        )
        run_id = cursor.lastrowid

        xp_earned = 0
        achievements = []

        if valid:
            # Calculate XP
            xp_earned = calculate_xp_for_run(distance_km, new_territory, False)

            # Save territory  
            if new_territory and territory_json:
                user_row = conn.execute("SELECT avatar_color FROM users WHERE id = ?", (user["id"],)).fetchone()
                conn.execute(
                    "INSERT INTO territories (user_id, polygon_json, area_sqm, color) VALUES (?, ?, ?, ?)",
                    (user["id"], territory_json, round(area_sqm, 2), user_row["avatar_color"])
                )

            # Update user stats
            conn.execute(
                """UPDATE users SET 
                    total_xp = total_xp + ?,
                    total_distance_km = total_distance_km + ?,
                    total_area_sqm = total_area_sqm + ?,
                    total_runs = total_runs + 1
                WHERE id = ?""",
                (xp_earned, round(distance_km, 3), round(area_sqm, 2) if new_territory else 0, user["id"])
            )

            # Update run with XP earned
            conn.execute("UPDATE runs SET xp_earned = ? WHERE id = ?", (xp_earned, run_id))

            # Update streak
            update_streak(user["id"], conn)

            # Update level and rank
            user_row = conn.execute("SELECT total_xp FROM users WHERE id = ?", (user["id"],)).fetchone()
            new_level = calculate_level(user_row["total_xp"])
            new_rank = get_rank(new_level)
            conn.execute("UPDATE users SET level = ?, rank = ? WHERE id = ?", (new_level, new_rank, user["id"]))

            conn.commit()

            # Check achievements
            achievements = check_and_award_achievements(user["id"], conn)

        conn.commit()

        # Build response
        analysis = get_cheat_analysis(features, cheat_score) if features else None

        return {
            "run_id": run_id,
            "distance_km": round(distance_km, 3),
            "duration_seconds": req.duration_seconds,
            "avg_speed_kmh": round(avg_speed, 2),
            "xp_earned": xp_earned,
            "territory_claimed": new_territory,
            "area_sqm": round(area_sqm, 2),
            "is_valid": valid,
            "cheat_analysis": analysis,
            "achievements_unlocked": achievements
        }
    finally:
        conn.close()


@router.get("/history")
async def get_run_history(user=Depends(get_current_user)):
    """Get user's run history."""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT id, start_time, end_time, duration_seconds, distance_km,
                      avg_speed_kmh, area_sqm, xp_earned, is_valid, cheat_score, created_at
               FROM runs WHERE user_id = ? ORDER BY created_at DESC LIMIT 50""",
            (user["id"],)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get("/{run_id}")
async def get_run_detail(run_id: int, user=Depends(get_current_user)):
    """Get detailed run info including path."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM runs WHERE id = ? AND user_id = ?",
            (run_id, user["id"])
        ).fetchone()
        if not row:
            raise HTTPException(404, "Run not found")
        result = dict(row)
        result["path"] = json.loads(result["path_json"]) if result["path_json"] else []
        result["territory_polygon"] = json.loads(result["territory_polygon_json"]) if result["territory_polygon_json"] else None
        return result
    finally:
        conn.close()
