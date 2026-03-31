"""
Database module — SQLite with all table definitions for RunConquer.
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "runconquer.db")


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            total_xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            rank TEXT DEFAULT 'Scout',
            total_area_sqm REAL DEFAULT 0.0,
            total_distance_km REAL DEFAULT 0.0,
            total_runs INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 0,
            last_run_date TEXT,
            avatar_color TEXT DEFAULT '#00f0ff',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL,
            distance_km REAL NOT NULL,
            avg_speed_kmh REAL NOT NULL,
            max_speed_kmh REAL DEFAULT 0.0,
            path_json TEXT NOT NULL,
            territory_polygon_json TEXT,
            area_sqm REAL DEFAULT 0.0,
            cheat_score REAL DEFAULT 0.0,
            is_valid INTEGER DEFAULT 1,
            xp_earned INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS territories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            polygon_json TEXT NOT NULL,
            area_sqm REAL NOT NULL,
            color TEXT DEFAULT '#00f0ff',
            created_at TEXT DEFAULT (datetime('now')),
            last_defended TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_key TEXT NOT NULL,
            unlocked_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, achievement_key)
        );
    """)

    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at {DB_PATH}")


# Achievement definitions
ACHIEVEMENTS = {
    "first_steps": {
        "name": "First Steps",
        "icon": "🏃",
        "description": "Complete your first run",
        "condition": lambda stats: stats["total_runs"] >= 1
    },
    "cartographer": {
        "name": "Cartographer",
        "icon": "🗺️",
        "description": "Claim 1 sq km of territory",
        "condition": lambda stats: stats["total_area_sqm"] >= 1_000_000
    },
    "on_fire": {
        "name": "On Fire",
        "icon": "🔥",
        "description": "7-day run streak",
        "condition": lambda stats: stats["streak_days"] >= 7
    },
    "marathoner": {
        "name": "Marathoner",
        "icon": "🏅",
        "description": "Run a total of 42.2 km",
        "condition": lambda stats: stats["total_distance_km"] >= 42.2
    },
    "speed_demon": {
        "name": "Speed Demon",
        "icon": "⚡",
        "description": "Average faster than 12 km/h in a run",
        "condition": lambda stats: stats.get("best_avg_speed", 0) >= 12
    },
    "land_baron": {
        "name": "Land Baron",
        "icon": "🏰",
        "description": "Own 5 separate territories",
        "condition": lambda stats: stats.get("territory_count", 0) >= 5
    },
    "world_dominator": {
        "name": "World Dominator",
        "icon": "🌍",
        "description": "Claim 10 sq km of territory",
        "condition": lambda stats: stats["total_area_sqm"] >= 10_000_000
    },
    "century_runner": {
        "name": "Century Runner",
        "icon": "💯",
        "description": "Complete 100 runs",
        "condition": lambda stats: stats["total_runs"] >= 100
    },
    "dedicated": {
        "name": "Dedicated",
        "icon": "💪",
        "description": "30-day run streak",
        "condition": lambda stats: stats["streak_days"] >= 30
    },
    "explorer": {
        "name": "Explorer",
        "icon": "🧭",
        "description": "Run a total of 100 km",
        "condition": lambda stats: stats["total_distance_km"] >= 100
    }
}
