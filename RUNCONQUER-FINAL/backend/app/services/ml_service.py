"""
RunConquer — ML Service (Upgraded)
====================================
Loads trained scikit-learn models for:
  1. Cheat Detection  — Random Forest classifier on GPS features
  2. Pace Prediction  — Ridge regression for performance forecasting

Falls back to rule-based heuristics if models aren't trained yet.
Run `python -m app.ml.train_model` to generate the model files.
"""

import os
import math
import numpy as np
from typing import List, Tuple, Optional
from app.services.geo_service import haversine_distance, calculate_speed

Point = Tuple[float, float]

# ─── Model paths ──────────────────────────────────────────────────────────────
_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "models")
_CHEAT_MODEL_PATH = os.path.join(_MODELS_DIR, "cheat_detector.pkl")
_PACE_MODEL_PATH = os.path.join(_MODELS_DIR, "pace_predictor.pkl")

_cheat_model = None
_pace_model = None


def _load_models():
    """Lazy-load models on first use."""
    global _cheat_model, _pace_model
    try:
        import joblib
        if _cheat_model is None and os.path.exists(_CHEAT_MODEL_PATH):
            _cheat_model = joblib.load(_CHEAT_MODEL_PATH)
        if _pace_model is None and os.path.exists(_PACE_MODEL_PATH):
            _pace_model = joblib.load(_PACE_MODEL_PATH)
    except Exception as e:
        print(f"[ml_service] Model load warning: {e}")


# ─── Feature Engineering ──────────────────────────────────────────────────────

FEATURE_NAMES = [
    "avg_speed", "max_speed", "speed_variance",
    "avg_acceleration", "max_acceleration",
    "gps_jump_count", "path_smoothness",
    "speed_cv", "pause_count",
    "total_distance_m", "duration_seconds",
]


def extract_features(path_points: List[Point], duration_seconds: float) -> Optional[dict]:
    """Extract 11 numerical features from a GPS path."""
    if len(path_points) < 3 or duration_seconds <= 0:
        return None

    num_segments = len(path_points) - 1
    time_per_segment = duration_seconds / num_segments

    speeds, distances = [], []
    for i in range(num_segments):
        dist = haversine_distance(path_points[i], path_points[i + 1])
        distances.append(dist)
        speed = (dist / 1000.0) / (time_per_segment / 3600.0) if time_per_segment > 0 else 0
        speeds.append(speed)

    speeds_arr = np.array(speeds)
    distances_arr = np.array(distances)

    avg_speed = float(np.mean(speeds_arr))
    max_speed = float(np.max(speeds_arr))
    speed_variance = float(np.var(speeds_arr))

    accelerations = np.abs(np.diff(speeds_arr)) if len(speeds_arr) > 1 else np.array([0.0])
    avg_acceleration = float(np.mean(accelerations))
    max_acceleration = float(np.max(accelerations))

    gps_jumps = int(np.sum(distances_arr > 100))
    total_distance = float(np.sum(distances_arr))
    direct_distance = haversine_distance(path_points[0], path_points[-1])
    path_smoothness = direct_distance / total_distance if total_distance > 0 else 0
    speed_cv = float(np.std(speeds_arr) / avg_speed) if avg_speed > 0 else 0
    pause_count = int(np.sum(speeds_arr < 0.5))

    return {
        "avg_speed": round(avg_speed, 2),
        "max_speed": round(max_speed, 2),
        "speed_variance": round(speed_variance, 2),
        "avg_acceleration": round(avg_acceleration, 2),
        "max_acceleration": round(max_acceleration, 2),
        "gps_jump_count": gps_jumps,
        "path_smoothness": round(path_smoothness, 4),
        "speed_cv": round(speed_cv, 4),
        "pause_count": pause_count,
        "total_distance_m": round(total_distance, 2),
        "duration_seconds": duration_seconds,
    }


def _features_to_vector(features: dict) -> np.ndarray:
    return np.array([[features[f] for f in FEATURE_NAMES]])


# ─── Cheat Detection ──────────────────────────────────────────────────────────

def calculate_cheat_score(features: dict) -> float:
    """Returns cheat probability. Uses trained RF if available, else rule-based fallback."""
    if features is None:
        return 0.5

    _load_models()

    if _cheat_model is not None:
        clf = _cheat_model["model"]
        X = _features_to_vector(features)
        prob = clf.predict_proba(X)[0][1]
        return round(float(prob), 3)
    else:
        return _rule_based_cheat_score(features)


def _rule_based_cheat_score(features: dict) -> float:
    score = 0.0
    checks = 5
    if features["max_speed"] > 45:
        score += 1.0
    elif features["max_speed"] > 30:
        score += 0.7
    elif features["max_speed"] > 20:
        score += 0.3
    if features["avg_speed"] > 25:
        score += 1.0
    elif features["avg_speed"] > 18:
        score += 0.5
    total_segs = max(1, int(features["total_distance_m"] / 50))
    jump_ratio = features["gps_jump_count"] / total_segs
    if jump_ratio > 0.3:
        score += 1.0
    elif jump_ratio > 0.1:
        score += 0.5
    if features["speed_variance"] < 0.5 and features["avg_speed"] > 10:
        score += 0.6
    if features["max_acceleration"] > 30:
        score += 0.8
    elif features["max_acceleration"] > 15:
        score += 0.4
    return round(min(1.0, score / checks), 3)


def is_run_valid(cheat_score: float, threshold: float = 0.4) -> bool:
    return cheat_score < threshold


def get_cheat_analysis(features: dict, cheat_score: float) -> dict:
    _load_models()
    model_used = "random_forest" if _cheat_model is not None else "rule_based_fallback"
    flags = []
    if features["max_speed"] > 30:
        flags.append(f"Max speed {features['max_speed']:.1f} km/h exceeds running limits")
    if features["avg_speed"] > 18:
        flags.append(f"Average speed {features['avg_speed']:.1f} km/h is suspiciously high")
    if features["gps_jump_count"] > 3:
        flags.append(f"{features['gps_jump_count']} GPS jumps detected (possible spoofing)")
    if features["max_acceleration"] > 15:
        flags.append(f"Extreme acceleration: {features['max_acceleration']:.1f} km/h per segment")
    if features["path_smoothness"] > 0.95 and features["total_distance_m"] > 1000:
        flags.append("Unnaturally straight path detected")
    return {
        "cheat_score": cheat_score,
        "is_valid": is_run_valid(cheat_score),
        "confidence": "high" if cheat_score > 0.7 or cheat_score < 0.2 else "medium",
        "model_used": model_used,
        "flags": flags,
        "features": features,
    }


# ─── Pace Prediction ──────────────────────────────────────────────────────────

def predict_pace(
    distance_km: float,
    elevation_gain_m: float = 0.0,
    avg_heart_rate: float = 150.0,
    temperature_c: float = 18.0,
    user_run_count: int = 1,
) -> dict:
    """Predict expected pace (min/km) using Ridge regression."""
    _load_models()

    if _pace_model is not None:
        pipe = _pace_model["model"]
        X = np.array([[distance_km, elevation_gain_m, avg_heart_rate,
                        temperature_c, float(user_run_count)]])
        pace = float(pipe.predict(X)[0])
    else:
        pace = 6.0 + (elevation_gain_m / 10) * 0.03

    pace = max(3.5, min(pace, 15.0))
    total_minutes = pace * distance_km

    if pace < 4.5:
        difficulty = "Elite"
    elif pace < 5.5:
        difficulty = "Advanced"
    elif pace < 7.0:
        difficulty = "Intermediate"
    elif pace < 9.0:
        difficulty = "Beginner"
    else:
        difficulty = "Walking"

    return {
        "predicted_pace_min_per_km": round(pace, 2),
        "estimated_finish_minutes": round(total_minutes, 1),
        "difficulty": difficulty,
        "model_used": "ridge_regression" if _pace_model is not None else "heuristic_fallback",
    }


# ─── Performance Trend Analysis ───────────────────────────────────────────────

def compute_performance_trend(run_history: list) -> dict:
    """
    Analyse run history for improvement trends using numpy linear regression (polyfit).
    Negative slope = runner is getting faster = good.
    """
    if len(run_history) < 3:
        return {"trend": "insufficient_data", "message": "Need at least 3 runs to analyse trend."}

    valid = [r for r in run_history if r.get("distance_km", 0) > 0 and r.get("duration_seconds", 0) > 0]
    if len(valid) < 3:
        return {"trend": "insufficient_data", "message": "Not enough valid runs."}

    paces = [(r["duration_seconds"] / 60.0) / r["distance_km"] for r in valid]
    x = np.arange(len(paces), dtype=float)
    slope, intercept = np.polyfit(x, paces, 1)

    if slope < -0.05:
        direction = "improving"
        message = f"Great progress! Pace improving by ~{abs(slope):.2f} min/km per run."
    elif slope > 0.05:
        direction = "declining"
        message = f"Pace declining by ~{slope:.2f} min/km per run. Consider rest or training adjustment."
    else:
        direction = "stable"
        message = "Pace is consistent. Ready to push harder?"

    return {
        "trend": direction,
        "slope_per_run": round(float(slope), 4),
        "avg_pace_min_per_km": round(float(np.mean(paces)), 2),
        "best_pace_min_per_km": round(float(min(paces)), 2),
        "message": message,
        "runs_analysed": len(valid),
    }
