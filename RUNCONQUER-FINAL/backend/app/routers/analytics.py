"""
Analytics Router — ML-powered performance endpoints.
New in upgraded version:
  POST /api/analytics/predict-pace   — Predict finish time for a planned run
  GET  /api/analytics/trend          — Personal improvement trend analysis
  GET  /api/analytics/model-info     — Which models are loaded + feature importances
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.routers.auth import get_current_user
from app.database import get_db
from app.services.ml_service import predict_pace, compute_performance_trend, _load_models, _cheat_model, _pace_model

router = APIRouter()


# ─── Request / Response Models ────────────────────────────────────────────────

class PacePredictionRequest(BaseModel):
    distance_km: float = Field(..., gt=0, le=200, description="Planned run distance in km")
    elevation_gain_m: float = Field(0.0, ge=0, description="Total elevation gain in metres")
    avg_heart_rate: float = Field(150.0, ge=60, le=220, description="Expected average heart rate (BPM)")
    temperature_c: float = Field(18.0, ge=-20, le=50, description="Ambient temperature in Celsius")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/predict-pace")
async def predict_run_pace(req: PacePredictionRequest, user=Depends(get_current_user)):
    """
    ML-powered pace prediction.
    Uses a trained Ridge Regression model that accounts for distance, elevation,
    heart rate, temperature, and the user's training history.
    """
    conn = get_db()
    try:
        run_count = conn.execute(
            "SELECT total_runs FROM users WHERE id = ?", (user["id"],)
        ).fetchone()
        user_run_count = run_count["total_runs"] if run_count else 1
    finally:
        conn.close()

    result = predict_pace(
        distance_km=req.distance_km,
        elevation_gain_m=req.elevation_gain_m,
        avg_heart_rate=req.avg_heart_rate,
        temperature_c=req.temperature_c,
        user_run_count=user_run_count,
    )
    return result


@router.get("/trend")
async def get_performance_trend(user=Depends(get_current_user)):
    """
    Analyse the user's pace over their last 20 valid runs.
    Returns trend direction (improving / stable / declining) computed via numpy polyfit.
    """
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT distance_km, duration_seconds, created_at
               FROM runs
               WHERE user_id = ? AND is_valid = 1 AND distance_km > 0
               ORDER BY created_at ASC
               LIMIT 20""",
            (user["id"],)
        ).fetchall()
        run_history = [dict(r) for r in rows]
    finally:
        conn.close()

    return compute_performance_trend(run_history)


@router.get("/model-info")
async def get_model_info():
    """
    Returns metadata about loaded ML models.
    Useful for the project README / demo — shows feature importances from the RF.
    """
    _load_models()

    cheat_info = {"status": "not_loaded"}
    pace_info = {"status": "not_loaded"}

    if _cheat_model is not None:
        clf = _cheat_model["model"]
        importances = dict(zip(
            _cheat_model["feature_names"],
            clf.feature_importances_.tolist()
        ))
        top_features = sorted(importances.items(), key=lambda x: -x[1])[:5]
        cheat_info = {
            "status": "loaded",
            "model_type": "RandomForestClassifier",
            "n_estimators": clf.n_estimators,
            "top_5_features": [{"feature": k, "importance": round(v, 4)} for k, v in top_features],
        }

    if _pace_model is not None:
        pace_info = {
            "status": "loaded",
            "model_type": "Ridge (via sklearn Pipeline with StandardScaler)",
            "feature_names": _pace_model["feature_names"],
        }

    return {
        "cheat_detector": cheat_info,
        "pace_predictor": pace_info,
        "instructions": "Run `python -m app.ml.train_model` to train models if not loaded.",
    }
