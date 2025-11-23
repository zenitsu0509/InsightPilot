import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

DATE_HINTS = ("date", "time", "month", "year", "period")
METRIC_HINTS = ("sale", "amount", "revenue", "profit", "price", "total")
MAX_POINTS = 60


def _detect_datetime_column(df: pd.DataFrame) -> Optional[str]:
    # Prefer columns already datetime typed
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    # Fallback to columns whose names hint at date/time
    for col in df.columns:
        low = col.lower()
        if any(hint in low for hint in DATE_HINTS):
            try:
                pd.to_datetime(df[col])
                return col
            except Exception:
                continue
    return None


def _detect_metric_column(df: pd.DataFrame) -> Optional[str]:
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric_cols:
        return None
    for col in numeric_cols:
        low = col.lower()
        if any(hint in low for hint in METRIC_HINTS):
            return col
    return numeric_cols[0]


def _build_time_series(df: pd.DataFrame) -> Optional[pd.Series]:
    if df is None or df.empty:
        return None

    date_col = _detect_datetime_column(df)
    metric_col = _detect_metric_column(df)
    if not date_col or not metric_col:
        return None

    ts = df[[date_col, metric_col]].copy()
    ts[date_col] = pd.to_datetime(ts[date_col], errors="coerce")
    ts = ts.dropna(subset=[date_col, metric_col])
    if ts.empty:
        return None

    # Aggregate by month for smoother signals
    ts["period"] = ts[date_col].dt.to_period("M").dt.to_timestamp()
    grouped = ts.groupby("period")[metric_col].sum().sort_index()
    if len(grouped) > MAX_POINTS:
        grouped = grouped[-MAX_POINTS:]
    return grouped


def _linear_trend(series: pd.Series) -> Optional[Dict[str, object]]:
    if series is None or len(series) < 3:
        return None

    x = np.arange(len(series))
    y = series.values.astype(float)
    slope, intercept = np.polyfit(x, y, 1)
    start_val = float(y[0])
    end_val = float(y[-1])
    change_pct = None
    if not math.isclose(start_val, 0.0):
        change_pct = ((end_val - start_val) / abs(start_val)) * 100

    direction = "flat"
    if slope > 0.02 * np.mean(y):
        direction = "upward"
    elif slope < -0.02 * np.mean(y):
        direction = "downward"

    summary = f"{direction.capitalize()} trend detected" if direction != "flat" else "Minimal trend detected"
    if change_pct is not None:
        summary += f" ({change_pct:+.1f}% over period)"

    return {
        "summary": summary,
        "start": start_val,
        "end": end_val,
        "slope": float(slope),
        "change_pct": change_pct,
        "points": [
            {"period": period.strftime("%Y-%m"), "value": float(value)}
            for period, value in series.items()
        ],
    }


def _anomaly_scan(series: pd.Series) -> Optional[Dict[str, object]]:
    if series is None or len(series) < 4:
        return None

    values = series.values.astype(float)
    mean = float(np.mean(values))
    std = float(np.std(values))
    if math.isclose(std, 0.0):
        return None

    z_scores = (values - mean) / std
    anomalies: List[Dict[str, object]] = []
    for idx, z in enumerate(z_scores):
        if abs(z) >= 2.0:
            period = series.index[idx]
            anomalies.append(
                {
                    "period": period.strftime("%Y-%m"),
                    "value": float(values[idx]),
                    "z_score": float(z),
                }
            )

    if not anomalies:
        return None

    top = sorted(anomalies, key=lambda a: abs(a["z_score"]), reverse=True)[:3]
    summary = "Anomalies detected at " + ", ".join(
        [f"{a['period']} (z={a['z_score']:+.1f})" for a in top]
    )

    return {"summary": summary, "anomalies": anomalies, "mean": mean, "std": std}


def run_advanced_analytics(df: pd.DataFrame) -> Dict[str, Optional[Dict[str, object]]]:
    series = _build_time_series(df)
    trend = _linear_trend(series)
    anomaly = _anomaly_scan(series)
    return {
        "trend": trend,
        "anomaly": anomaly,
    }
