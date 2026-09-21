"""
Smart Attendance - AI service (OPTIONAL / EXTRA)
==================================================

This service is intentionally separate from the main backend.
If it is down, slow, or never started, the core app (auth, sessions,
QR scan, attendance recording, roster, corrections, reports) must keep
working exactly as before. This service only adds two extra things on
top: a risk score per student, and a list of anomaly flags.

Run:
    pip install -r requirements.txt
    python train_model.py          # produces risk_model.pkl (run once, offline)
    uvicorn main:app --reload --port 8001

Then check http://localhost:8001/docs
"""

from contextlib import asynccontextmanager
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from train_model import FEATURES, build_weekly_features, load_and_clean, MODEL_FILE

DATA_FILE = "attendance_history.csv"

# In-memory cache. Recomputed on startup and whenever /refresh is called.
state = {
    "model": None,
    "weekly_latest": None,   # latest week's feature row per student
    "anomaly_report": None,  # per-student anomaly flags
    "ready": False,
}


def probability_to_risk(probability: float) -> str:
    if probability >= 0.70:
        return "HIGH"
    if probability >= 0.40:
        return "MEDIUM"
    return "LOW"


def explain(row: pd.Series) -> str:
    reasons = []
    if row["previous_attendance"] < 0.70:
        reasons.append("Previous attendance is below 70%")
    if row["recent_3week_attendance"] < 0.70:
        reasons.append("Recent 3-week attendance is below 70%")
    if row["previous_late_rate"] >= 0.30:
        reasons.append("High late-attendance rate")
    if row["previous_absence_rate"] >= 0.30:
        reasons.append("High absence rate")
    if row["attendance_trend"] < 0:
        reasons.append("Attendance trend is decreasing")
    if not reasons:
        reasons.append("No major rule-based risk factor detected")
    return "; ".join(reasons)


def build_anomaly_report(df: pd.DataFrame) -> pd.DataFrame:
    late_summary = (
        df.groupby("student_code")
        .agg(total_records=("attendance_status", "count"), late_count=("is_late", "sum"))
        .reset_index()
    )
    late_summary["late_rate"] = np.where(
        late_summary["total_records"] > 0,
        late_summary["late_count"] / late_summary["total_records"],
        0,
    )
    late_summary["repeated_late_flag"] = (late_summary["late_count"] >= 3).astype(int)

    attendance_summary = (
        df.groupby("student_code")
        .agg(
            attended_sessions=("attended", "sum"),
            counted_sessions=("counted_session", "sum"),
        )
        .reset_index()
    )
    attendance_summary["attendance_rate"] = np.where(
        attendance_summary["counted_sessions"] > 0,
        attendance_summary["attended_sessions"] / attendance_summary["counted_sessions"],
        np.nan,
    )
    attendance_summary["low_attendance_flag"] = (
        attendance_summary["attendance_rate"] < 0.70
    ).fillna(False).astype(int)

    if "source" in df.columns:
        manual_flag = df["source"].astype(str).str.strip().str.lower().eq("manual")
    else:
        manual_flag = pd.Series(False, index=df.index)
    df = df.assign(manual_entry_flag=manual_flag.astype(int))
    manual_summary = (
        df.groupby("student_code").agg(manual_entry_count=("manual_entry_flag", "sum")).reset_index()
    )

    report = attendance_summary.merge(late_summary, on="student_code", how="left")
    report = report.merge(manual_summary, on="student_code", how="left")
    report["manual_review_flag"] = (report["manual_entry_count"] > 0).astype(int)
    report["anomaly_flag"] = (
        (report["low_attendance_flag"] == 1)
        | (report["repeated_late_flag"] == 1)
        | (report["manual_review_flag"] == 1)
    ).astype(int)

    return report


def refresh_state():
    """Recompute everything from the current CSV. Safe to call anytime."""
    try:
        model = joblib.load(MODEL_FILE)
    except FileNotFoundError:
        state["ready"] = False
        state["model"] = None
        return

    df = load_and_clean(DATA_FILE)
    weekly = build_weekly_features(df)

    # Latest available feature row per student (for live /risk lookups)
    latest = (
        weekly.dropna(subset=FEATURES)
        .sort_values(["student_code", "week_number"])
        .groupby("student_code")
        .tail(1)
        .set_index("student_code")
    )

    state["model"] = model
    state["weekly_latest"] = latest
    state["anomaly_report"] = build_anomaly_report(df).set_index("student_code")
    state["ready"] = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    refresh_state()  # best-effort; service still starts if this fails
    yield


app = FastAPI(title="Smart Attendance - AI Service", lifespan=lifespan)


class RiskResponse(BaseModel):
    student_code: str
    risk_probability: float
    risk_level: str
    explanation: str


@app.get("/health")
def health():
    return {"status": "ok", "model_ready": state["ready"]}


@app.post("/refresh")
def refresh():
    refresh_state()
    return {"status": "refreshed", "model_ready": state["ready"]}


@app.get("/risk/{student_code}", response_model=RiskResponse)
def get_risk(student_code: str):
    if not state["ready"]:
        raise HTTPException(status_code=503, detail="AI model not available")

    latest = state["weekly_latest"]
    if student_code not in latest.index:
        raise HTTPException(status_code=404, detail="No recent data for this student")

    row = latest.loc[student_code]
    x = row[FEATURES].to_frame().T
    probability = float(state["model"].predict_proba(x)[0, 1])

    return RiskResponse(
        student_code=student_code,
        risk_probability=round(probability, 4),
        risk_level=probability_to_risk(probability),
        explanation=explain(row),
    )


@app.get("/anomalies")
def get_anomalies(limit: Optional[int] = 50):
    if not state["ready"]:
        raise HTTPException(status_code=503, detail="AI model not available")

    report = state["anomaly_report"]
    flagged = report[report["anomaly_flag"] == 1].reset_index()
    return flagged.head(limit).to_dict(orient="records")
