"""
RunConquer — ML Training Pipeline
==================================
Generates synthetic GPS run data, trains a Random Forest classifier
for cheat detection, and a Linear Regression model for pace prediction.

Run this script once to generate trained model files:
    python -m app.ml.train_model

Author note (for interview): This pipeline simulates the real-world flow of:
  1. Data collection (synthetic but statistically realistic)
  2. Feature engineering  
  3. Model training with cross-validation
  4. Serialization with joblib
"""

import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

# ─── Constants ────────────────────────────────────────────────────────────────
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
CHEAT_MODEL_PATH = os.path.join(MODELS_DIR, "cheat_detector.pkl")
PACE_MODEL_PATH = os.path.join(MODELS_DIR, "pace_predictor.pkl")
RANDOM_SEED = 42

FEATURE_NAMES = [
    "avg_speed",
    "max_speed",
    "speed_variance",
    "avg_acceleration",
    "max_acceleration",
    "gps_jump_count",
    "path_smoothness",
    "speed_cv",
    "pause_count",
    "total_distance_m",
    "duration_seconds",
]


# ─── Synthetic Data Generator ─────────────────────────────────────────────────

def _generate_legitimate_run(rng: np.random.Generator) -> dict:
    """Simulate a real human run. Speed drawn from realistic running distributions."""
    # Elite: 15-20 km/h, recreational: 8-12 km/h, jogger: 5-8 km/h
    profile = rng.choice(["elite", "recreational", "jogger"], p=[0.1, 0.55, 0.35])
    base_speeds = {"elite": (16, 2.5), "recreational": (10, 1.5), "jogger": (7, 1.0)}
    mu, sigma = base_speeds[profile]

    n_segments = rng.integers(20, 80)
    speeds = np.clip(rng.normal(mu, sigma, n_segments), 4.0, 22.0)

    # Humans slow down on hills, stop at lights — add natural pauses
    pause_mask = rng.random(n_segments) < 0.08
    speeds[pause_mask] = rng.uniform(0, 0.5, pause_mask.sum())

    avg_speed = float(np.mean(speeds))
    max_speed = float(np.max(speeds))
    speed_variance = float(np.var(speeds))
    accelerations = np.abs(np.diff(speeds))
    avg_acc = float(np.mean(accelerations)) if len(accelerations) > 0 else 0.0
    max_acc = float(np.max(accelerations)) if len(accelerations) > 0 else 0.0

    duration_s = rng.uniform(900, 7200)  # 15 min to 2 hours
    total_dist = avg_speed * (duration_s / 3600) * 1000  # metres

    return {
        "avg_speed": avg_speed,
        "max_speed": max_speed,
        "speed_variance": speed_variance,
        "avg_acceleration": avg_acc,
        "max_acceleration": max_acc,
        "gps_jump_count": int(rng.integers(0, 3)),
        "path_smoothness": float(rng.uniform(0.3, 0.85)),
        "speed_cv": float(np.std(speeds) / np.mean(speeds)) if np.mean(speeds) > 0 else 0,
        "pause_count": int(pause_mask.sum()),
        "total_distance_m": total_dist,
        "duration_seconds": duration_s,
        "label": 0,  # legitimate
    }


def _generate_cheating_run(rng: np.random.Generator, cheat_type: str) -> dict:
    """Simulate a cheating run. Three realistic cheat patterns."""
    if cheat_type == "driving":
        speeds = np.clip(rng.normal(40, 8, rng.integers(15, 40)), 20, 80)
        gps_jumps = int(rng.integers(0, 4))
        smoothness = float(rng.uniform(0.75, 0.98))
    elif cheat_type == "gps_spoof":
        speeds = np.clip(rng.normal(10, 1.0, rng.integers(20, 50)), 5, 15)
        gps_jumps = int(rng.integers(8, 25))   # many jumps = teleportation
        smoothness = float(rng.uniform(0.85, 1.0))  # unnaturally straight
    else:  # speed_hack — edited timestamps
        speeds = np.clip(rng.normal(25, 5, rng.integers(20, 60)), 12, 50)
        gps_jumps = int(rng.integers(0, 5))
        smoothness = float(rng.uniform(0.5, 0.9))

    avg_speed = float(np.mean(speeds))
    max_speed = float(np.max(speeds))
    speed_variance = float(np.var(speeds))
    accelerations = np.abs(np.diff(speeds))
    avg_acc = float(np.mean(accelerations)) if len(accelerations) > 0 else 0.0
    max_acc = float(np.max(accelerations)) if len(accelerations) > 0 else 0.0

    duration_s = rng.uniform(600, 3600)
    total_dist = avg_speed * (duration_s / 3600) * 1000

    return {
        "avg_speed": avg_speed,
        "max_speed": max_speed,
        "speed_variance": speed_variance,
        "avg_acceleration": avg_acc,
        "max_acceleration": max_acc,
        "gps_jump_count": gps_jumps,
        "path_smoothness": smoothness,
        "speed_cv": float(np.std(speeds) / np.mean(speeds)) if np.mean(speeds) > 0 else 0,
        "pause_count": 0,
        "total_distance_m": total_dist,
        "duration_seconds": duration_s,
        "label": 1,  # cheat
    }


def generate_dataset(n_legit: int = 1500, n_cheat: int = 500, seed: int = RANDOM_SEED):
    """
    Build a balanced-ish synthetic dataset.
    Returns X (feature matrix) and y (labels).
    """
    rng = np.random.default_rng(seed)
    rows = []

    for _ in range(n_legit):
        rows.append(_generate_legitimate_run(rng))

    cheat_types = ["driving", "gps_spoof", "speed_hack"]
    for i in range(n_cheat):
        rows.append(_generate_cheating_run(rng, cheat_types[i % 3]))

    X = np.array([[r[f] for f in FEATURE_NAMES] for r in rows])
    y = np.array([r["label"] for r in rows])
    return X, y


# ─── Cheat Detector Training ──────────────────────────────────────────────────

def train_cheat_detector():
    """
    Train a Random Forest classifier and save it.
    Cross-validation ensures we're not just memorising training data.
    """
    print("Generating synthetic run dataset...")
    X, y = generate_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )

    # Random Forest: good default for tabular sensor data, interpretable via feature importance
    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=10,
        min_samples_leaf=4,
        class_weight="balanced",  # handle class imbalance
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )

    # 5-fold stratified CV to check generalisation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    cv_scores = cross_val_score(clf, X_train, y_train, cv=cv, scoring="f1")
    print(f"  Cross-val F1: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    clf.fit(X_train, y_train)

    print("\n  Test set performance:")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["Legit", "Cheat"]))

    # Feature importances for explainability (great talking point in interviews)
    importances = dict(zip(FEATURE_NAMES, clf.feature_importances_))
    top3 = sorted(importances.items(), key=lambda x: -x[1])[:3]
    print(f"  Top-3 features: {top3}")

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump({"model": clf, "feature_names": FEATURE_NAMES}, CHEAT_MODEL_PATH)
    print(f"  Saved → {CHEAT_MODEL_PATH}")
    return clf


# ─── Pace Predictor Training ─────────────────────────────────────────────────

def _generate_pace_dataset(n: int = 2000, seed: int = RANDOM_SEED):
    """
    Synthetic dataset for pace prediction (regression).
    Features: distance, elevation gain, avg heart rate (simulated), temperature, run_number
    Target: avg_pace_per_km (minutes)
    """
    rng = np.random.default_rng(seed)

    distance_km = rng.uniform(1, 42, n)          # 1 km sprint to marathon
    elevation_gain_m = rng.uniform(0, 600, n)     # flat to hilly
    heart_rate = rng.uniform(120, 185, n)          # bpm
    temperature_c = rng.uniform(-5, 38, n)         # extreme temps slow you down
    run_number = rng.integers(1, 300, n).astype(float)  # fitness improves over time

    # Pace model: realistic human physiology approximation
    base_pace = 6.0  # 6 min/km baseline
    pace = (
        base_pace
        + 0.03 * elevation_gain_m / 10         # hills slow you
        + 0.008 * (heart_rate - 150)            # higher effort = faster but tiring
        + 0.02 * np.maximum(temperature_c - 20, 0)  # heat slows
        + 0.03 * np.maximum(10 - temperature_c, 0)  # cold also slows
        - 0.003 * run_number                    # fitness improvement over time
        + rng.normal(0, 0.3, n)                 # individual variability
    )
    pace = np.clip(pace, 3.5, 12.0)  # physical limits

    X = np.column_stack([distance_km, elevation_gain_m, heart_rate, temperature_c, run_number])
    return X, pace


def train_pace_predictor():
    """
    Train a Ridge regression model to predict pace (min/km).
    Uses sklearn Pipeline with StandardScaler — important for regularised regression.
    """
    print("\nGenerating pace prediction dataset...")
    X, y = _generate_pace_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("model", Ridge(alpha=1.0))
    ])

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"  MAE: {mae:.3f} min/km  |  R²: {r2:.3f}")

    pace_feature_names = ["distance_km", "elevation_gain_m", "heart_rate", "temperature_c", "run_number"]
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump({"model": pipe, "feature_names": pace_feature_names}, PACE_MODEL_PATH)
    print(f"  Saved → {PACE_MODEL_PATH}")
    return pipe


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("RunConquer ML Training Pipeline")
    print("=" * 60)
    train_cheat_detector()
    train_pace_predictor()
    print("\nDone. Models saved to app/ml/models/")
