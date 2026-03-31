"""
Gamification Service — XP, levels, ranks, achievements, streaks.
"""
import math
from datetime import datetime, timedelta
from app.database import get_db, ACHIEVEMENTS


# --- XP & Leveling ---

XP_PER_RUN = 100
XP_PER_KM = 50
XP_NEW_TERRITORY = 200
XP_TERRITORY_DEFENDED = 150
XP_ACHIEVEMENT = 300


def calculate_xp_for_run(distance_km: float, new_territory: bool, territory_defended: bool) -> int:
    """Calculate XP earned for a run."""
    xp = XP_PER_RUN
    xp += int(distance_km * XP_PER_KM)
    if new_territory:
        xp += XP_NEW_TERRITORY
    if territory_defended:
        xp += XP_TERRITORY_DEFENDED
    return xp


def calculate_level(total_xp: int) -> int:
    """Level = floor(sqrt(totalXP / 100))"""
    if total_xp <= 0:
        return 1
    return max(1, int(math.floor(math.sqrt(total_xp / 100))))


def get_rank(level: int) -> str:
    """Get rank based on level."""
    if level >= 51:
        return "Emperor"
    elif level >= 31:
        return "Warlord"
    elif level >= 16:
        return "Conqueror"
    elif level >= 6:
        return "Explorer"
    else:
        return "Scout"


def get_rank_icon(rank: str) -> str:
    """Get rank icon."""
    icons = {
        "Scout": "🥉",
        "Explorer": "🥈",
        "Conqueror": "🥇",
        "Warlord": "💎",
        "Emperor": "👑"
    }
    return icons.get(rank, "🥉")


def xp_for_next_level(current_level: int) -> int:
    """Calculate XP needed to reach next level."""
    return ((current_level + 1) ** 2) * 100


def xp_progress_percent(total_xp: int) -> float:
    """Get progress percentage towards next level."""
    level = calculate_level(total_xp)
    current_level_xp = (level ** 2) * 100
    next_level_xp = ((level + 1) ** 2) * 100
    if next_level_xp == current_level_xp:
        return 100.0
    return ((total_xp - current_level_xp) / (next_level_xp - current_level_xp)) * 100


# --- Streaks ---

def update_streak(user_id: int, conn=None):
    """Update user's streak based on last run date."""
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        row = conn.execute(
            "SELECT streak_days, last_run_date FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not row:
            return 0

        today = datetime.utcnow().strftime("%Y-%m-%d")
        last_run = row["last_run_date"]

        if last_run == today:
            return row["streak_days"]
        elif last_run:
            last_date = datetime.strptime(last_run, "%Y-%m-%d")
            yesterday = datetime.utcnow() - timedelta(days=1)
            if last_date.strftime("%Y-%m-%d") == yesterday.strftime("%Y-%m-%d"):
                new_streak = row["streak_days"] + 1
            else:
                new_streak = 1
        else:
            new_streak = 1

        # Calculate streak XP bonus
        streak_xp = new_streak * 25

        conn.execute(
            "UPDATE users SET streak_days = ?, last_run_date = ?, total_xp = total_xp + ? WHERE id = ?",
            (new_streak, today, streak_xp, user_id)
        )
        conn.commit()
        return new_streak
    finally:
        if close_conn:
            conn.close()


# --- Achievements ---

def check_and_award_achievements(user_id: int, conn=None) -> list:
    """Check and award any new achievements for user. Returns list of newly unlocked."""
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        # Get user stats
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return []

        # Get territory count
        territory_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM territories WHERE user_id = ?",
            (user_id,)
        ).fetchone()["cnt"]

        # Get best avg speed
        best_speed = conn.execute(
            "SELECT MAX(avg_speed_kmh) as best FROM runs WHERE user_id = ? AND is_valid = 1",
            (user_id,)
        ).fetchone()

        stats = {
            "total_runs": user["total_runs"],
            "total_area_sqm": user["total_area_sqm"],
            "total_distance_km": user["total_distance_km"],
            "streak_days": user["streak_days"],
            "territory_count": territory_count,
            "best_avg_speed": best_speed["best"] if best_speed["best"] else 0
        }

        # Get already unlocked achievements
        existing = conn.execute(
            "SELECT achievement_key FROM achievements WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        existing_keys = {r["achievement_key"] for r in existing}

        # Check each achievement
        newly_unlocked = []
        for key, ach in ACHIEVEMENTS.items():
            if key not in existing_keys and ach["condition"](stats):
                conn.execute(
                    "INSERT INTO achievements (user_id, achievement_key) VALUES (?, ?)",
                    (user_id, key)
                )
                conn.execute(
                    "UPDATE users SET total_xp = total_xp + ? WHERE id = ?",
                    (XP_ACHIEVEMENT, user_id)
                )
                newly_unlocked.append({
                    "key": key,
                    "name": ach["name"],
                    "icon": ach["icon"],
                    "description": ach["description"]
                })

        if newly_unlocked:
            conn.commit()

        # Update level and rank
        updated_user = conn.execute("SELECT total_xp FROM users WHERE id = ?", (user_id,)).fetchone()
        new_level = calculate_level(updated_user["total_xp"])
        new_rank = get_rank(new_level)
        conn.execute(
            "UPDATE users SET level = ?, rank = ? WHERE id = ?",
            (new_level, new_rank, user_id)
        )
        conn.commit()

        return newly_unlocked
    finally:
        if close_conn:
            conn.close()


def get_user_achievements(user_id: int) -> list:
    """Get all achievements for a user (unlocked and locked)."""
    conn = get_db()
    try:
        unlocked = conn.execute(
            "SELECT achievement_key, unlocked_at FROM achievements WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        unlocked_map = {r["achievement_key"]: r["unlocked_at"] for r in unlocked}

        result = []
        for key, ach in ACHIEVEMENTS.items():
            result.append({
                "key": key,
                "name": ach["name"],
                "icon": ach["icon"],
                "description": ach["description"],
                "unlocked": key in unlocked_map,
                "unlocked_at": unlocked_map.get(key)
            })
        return result
    finally:
        conn.close()
