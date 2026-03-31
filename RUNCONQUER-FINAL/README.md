# RunConquer — Gamified Territory Running App
### *Upgraded for AI/ML Placement Preparation*

---

## What this project demonstrates (for recruiters)

| Skill | Where |
|---|---|
| REST API design (FastAPI, JWT auth) | `backend/app/routers/` |
| Scikit-learn ML pipeline (train → serve) | `app/ml/train_model.py` |
| Random Forest classification | `ml_service.py → calculate_cheat_score()` |
| Ridge regression with sklearn Pipeline | `ml_service.py → predict_pace()` |
| Feature engineering from GPS sensor data | `ml_service.py → extract_features()` |
| Cross-validation + model evaluation | `train_model.py → train_cheat_detector()` |
| Computational geometry (Convex Hull, Haversine) | `geo_service.py` |
| Gamification system (XP, levels, streaks) | `game_service.py` |
| SQLite with connection pooling | `database.py` |

---

## Project Overview

RunConquer is a location-based running game where players physically run routes to "conquer" territories on a real map. The backend uses **ML for cheat detection** (identifying GPS spoofing and driving-while-running) and **pace prediction** (forecasting your finish time based on route conditions).

---

## ML Components

### 1. Cheat Detection — Random Forest Classifier

**File:** `app/ml/train_model.py` → `train_cheat_detector()`

Detects three types of cheating from GPS data:
- **Driving** — high average speed, low speed variance (cruise control pattern)
- **GPS Spoofing** — sudden coordinate jumps, unnaturally straight paths
- **Timestamp editing** — unrealistic accelerations between points

**Features used (11 total):**
```
avg_speed, max_speed, speed_variance,
avg_acceleration, max_acceleration,
gps_jump_count, path_smoothness,
speed_cv, pause_count,
total_distance_m, duration_seconds
```

**Training:**
```bash
cd backend
python -m app.ml.train_model
```

**Output:** Cross-validation F1 + classification report + top-3 feature importances

### 2. Pace Prediction — Ridge Regression

**File:** `app/ml/train_model.py` → `train_pace_predictor()`

Predicts expected pace (min/km) for a planned run given:
- Distance, elevation gain
- Expected heart rate
- Temperature
- User's training history (run count as fitness proxy)

Uses `sklearn.Pipeline` with `StandardScaler` + `Ridge(alpha=1.0)`.

### 3. Performance Trend Analysis

**File:** `app/services/ml_service.py` → `compute_performance_trend()`

Uses `numpy.polyfit` to compute linear regression over a user's pace history.
- Negative slope → runner improving
- Positive slope → declining performance

---

## API Endpoints

### New in v2 (AI/ML upgrade)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analytics/predict-pace` | Predict pace for a planned run |
| `GET` | `/api/analytics/trend` | Get personal improvement trend |
| `GET` | `/api/analytics/model-info` | RF feature importances + model metadata |

### Core endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Login → JWT token |
| `POST` | `/api/runs/submit` | Submit GPS run (triggers ML cheat check) |
| `GET` | `/api/runs/history` | Run history |
| `GET` | `/api/territories/all` | All territory polygons (for map) |
| `GET` | `/api/leaderboard` | Global leaderboard |

---

## Setup & Running

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Train ML models (generates cheat_detector.pkl + pace_predictor.pkl)
python -m app.ml.train_model

# 3. Start the server
uvicorn app.main:app --reload --port 8000

# 4. Visit http://localhost:8000
# API docs at http://localhost:8000/docs
```

---

## Architecture

```
runconquer/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app + router registration
│       ├── database.py          # SQLite setup + schema + achievements
│       ├── ml/
│       │   ├── train_model.py   # ← DATA PIPELINE + MODEL TRAINING
│       │   └── models/
│       │       ├── cheat_detector.pkl   # trained RF model
│       │       └── pace_predictor.pkl   # trained Ridge model
│       ├── services/
│       │   ├── ml_service.py    # ← ML INFERENCE (loads .pkl, serves predictions)
│       │   ├── geo_service.py   # Haversine, convex hull, Shoelace area
│       │   └── game_service.py  # XP, levels, streaks, achievements
│       └── routers/
│           ├── auth.py          # JWT auth
│           ├── runs.py          # Run submission + cheat detection
│           ├── territories.py   # Territory CRUD
│           ├── leaderboard.py   # Rankings
│           └── analytics.py     # ← NEW: ML-powered analytics
└── frontend/
    └── templates/              # Jinja2 HTML pages
```

---

## Interview Talking Points

1. **Why Random Forest for cheat detection?**
   - Handles mixed feature types (count-based GPS jumps + continuous speeds)
   - `class_weight='balanced'` handles imbalanced data (few cheaters vs many legit runs)
   - Built-in `feature_importances_` for explainability (important in production ML)
   - Robust to outliers without feature scaling

2. **Why Ridge Regression for pace prediction?**
   - Linear relationship between features and pace is physiologically reasonable
   - L2 regularisation prevents overfitting on correlated features (distance ↔ duration)
   - `StandardScaler` in Pipeline ensures correct scaling at train AND inference time

3. **How do you handle the cold-start problem (no training data)?**
   - The `train_model.py` generates statistically realistic synthetic data
   - Service falls back to rule-based heuristics if models aren't yet trained
   - In a real app, you'd bootstrap with synthetic data then continuously retrain on real data

4. **What metrics did you evaluate on?**
   - Cheat detection: F1-score (because precision + recall both matter — false positives unfairly penalise players, false negatives let cheaters win)
   - Pace prediction: MAE (interpretable in minutes) + R² (variance explained)
