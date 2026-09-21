"""
Train the low-attendance risk model and save it to disk.

This is the SAME logic as the notebook (ai_task_grad.ipynb), just trimmed
down to the parts needed to produce a reusable model file. Run this
offline, whenever you have new/updated attendance_history.csv data —
NOT on every request.

Usage:
    python train_model.py

Output:
    risk_model.pkl   <- load this in main.py
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DATA_FILE = "attendance_history.csv"
MODEL_FILE = "risk_model.pkl"

LOW_ATTENDANCE_THRESHOLD = 0.70
TRAIN_LAST_WEEK = 9

FEATURES = [
    "previous_attendance",
    "recent_3week_attendance",
    "previous_late_rate",
    "previous_absence_rate",
    "previous_course_load",
    "attendance_trend",
]


def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    df["session_date"] = pd.to_datetime(df["session_date"], errors="coerce")
    df["week_number"] = pd.to_numeric(df["week_number"], errors="coerce")
    df["course_load"] = pd.to_numeric(df["course_load"], errors="coerce")
    df["attendance_status"] = (
        df["attendance_status"].astype(str).str.strip().str.lower()
    )

    df = df.dropna(
        subset=["session_date", "student_code", "week_number", "attendance_status"]
    )
    df["course_load"] = df["course_load"].fillna(df["course_load"].median())
    df = df.drop_duplicates()
    df = df.sort_values(["student_code", "session_date"]).reset_index(drop=True)

    df["attended"] = df["attendance_status"].isin(["present", "late"]).astype(int)
    df["is_late"] = (df["attendance_status"] == "late").astype(int)
    df["is_absent"] = (df["attendance_status"] == "absent").astype(int)
    df["counted_session"] = (
        df["attendance_status"].isin(["present", "late", "absent"]).astype(int)
    )

    return df


def build_weekly_features(df: pd.DataFrame) -> pd.DataFrame:
    weekly = (
        df.groupby(["student_code", "week_number"])
        .agg(
            attended=("attended", "sum"),
            late=("is_late", "sum"),
            absent=("is_absent", "sum"),
            counted_sessions=("counted_session", "sum"),
            avg_course_load=("course_load", "mean"),
        )
        .reset_index()
    )

    weekly["attendance_rate"] = np.where(
        weekly["counted_sessions"] > 0,
        weekly["attended"] / weekly["counted_sessions"],
        np.nan,
    )
    weekly["late_rate"] = np.where(
        weekly["counted_sessions"] > 0, weekly["late"] / weekly["counted_sessions"], 0
    )
    weekly["absence_rate"] = np.where(
        weekly["counted_sessions"] > 0,
        weekly["absent"] / weekly["counted_sessions"],
        0,
    )

    weekly = weekly.sort_values(["student_code", "week_number"]).reset_index(
        drop=True
    )

    g = weekly.groupby("student_code")
    weekly["previous_attendance"] = g["attendance_rate"].shift(1)
    weekly["previous_late_rate"] = g["late_rate"].shift(1)
    weekly["previous_absence_rate"] = g["absence_rate"].shift(1)
    weekly["previous_course_load"] = g["avg_course_load"].shift(1)
    weekly["recent_3week_attendance"] = g["attendance_rate"].transform(
        lambda values: values.shift(1).rolling(window=3, min_periods=1).mean()
    )
    weekly["attendance_trend"] = (
        weekly["previous_attendance"] - weekly["recent_3week_attendance"]
    )

    next_week_table = weekly[["student_code", "week_number", "attendance_rate"]].rename(
        columns={
            "week_number": "next_week_number",
            "attendance_rate": "next_week_attendance",
        }
    )
    weekly["next_week_number"] = weekly["week_number"] + 1
    weekly = weekly.merge(
        next_week_table, on=["student_code", "next_week_number"], how="left"
    )
    weekly["low_attendance_next_week"] = (
        weekly["next_week_attendance"] < LOW_ATTENDANCE_THRESHOLD
    ).astype(int)

    return weekly


def main():
    df = load_and_clean(DATA_FILE)
    weekly = build_weekly_features(df)

    model_df = weekly.dropna(subset=FEATURES + ["next_week_attendance"]).copy()
    model_df = model_df.sort_values(["week_number", "student_code"]).reset_index(
        drop=True
    )

    train_df = model_df[model_df["week_number"] <= TRAIN_LAST_WEEK]
    X_train = train_df[FEATURES]
    y_train = train_df["low_attendance_next_week"]

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "logistic_regression",
                LogisticRegression(max_iter=2000, random_state=42),
            ),
        ]
    )
    model.fit(X_train, y_train)

    joblib.dump(model, MODEL_FILE)
    print(f"Saved trained model to {MODEL_FILE}")
    print(f"Trained on {len(train_df)} rows, weeks 1-{TRAIN_LAST_WEEK}")


if __name__ == "__main__":
    main()
