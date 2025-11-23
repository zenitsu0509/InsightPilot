import math
from typing import Dict, List, Optional, Tuple
import warnings

import numpy as np
import pandas as pd
from scipy import stats

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.stattools import adfuller
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

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
    
    # Linear regression with confidence intervals
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    
    # Calculate standard error and confidence intervals
    residuals = y - y_pred
    n = len(y)
    degrees_freedom = n - 2
    residual_std_error = np.sqrt(np.sum(residuals**2) / degrees_freedom) if degrees_freedom > 0 else 0
    
    # Standard error of slope
    x_mean = np.mean(x)
    se_slope = residual_std_error / np.sqrt(np.sum((x - x_mean)**2)) if np.sum((x - x_mean)**2) > 0 else 0
    
    # 95% confidence interval for slope
    t_val = stats.t.ppf(0.975, degrees_freedom) if degrees_freedom > 0 else 1.96
    slope_ci_lower = slope - t_val * se_slope
    slope_ci_upper = slope + t_val * se_slope
    
    # Prediction intervals for the trend line
    prediction_intervals = []
    for i in range(len(x)):
        se_pred = residual_std_error * np.sqrt(1 + 1/n + (x[i] - x_mean)**2 / np.sum((x - x_mean)**2))
        pi_lower = y_pred[i] - t_val * se_pred
        pi_upper = y_pred[i] + t_val * se_pred
        prediction_intervals.append({
            "lower": float(pi_lower),
            "upper": float(pi_upper)
        })
    
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
    summary += f" with 95% confidence [slope: {slope_ci_lower:.2f} to {slope_ci_upper:.2f}]"

    return {
        "summary": summary,
        "start": start_val,
        "end": end_val,
        "slope": float(slope),
        "slope_ci_lower": float(slope_ci_lower),
        "slope_ci_upper": float(slope_ci_upper),
        "std_error": float(residual_std_error),
        "r_squared": float(1 - np.sum(residuals**2) / np.sum((y - np.mean(y))**2)) if np.sum((y - np.mean(y))**2) > 0 else 0,
        "change_pct": change_pct,
        "points": [
            {"period": period.strftime("%Y-%m"), "value": float(value)}
            for period, value in series.items()
        ],
        "prediction_intervals": prediction_intervals,
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
    forecast = _forecast_next_periods(series)
    statistical_tests = _run_statistical_tests(series)
    return {
        "trend": trend,
        "anomaly": anomaly,
        "forecast": forecast,
        "statistical_tests": statistical_tests,
    }


def _forecast_next_periods(series: pd.Series, periods: int = 3) -> Optional[Dict[str, object]]:
    """Generate forecasts using exponential smoothing with prediction intervals."""
    if series is None or len(series) < 6:
        return None
    
    if not HAS_STATSMODELS:
        return {
            "summary": "Forecasting unavailable (statsmodels not installed)",
            "forecasts": [],
        }
    
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # Try Holt's exponential smoothing (trend method)
            model = ExponentialSmoothing(
                series.values,
                trend='add',
                seasonal=None,
                initialization_method="estimated"
            )
            fitted = model.fit(optimized=True, remove_bias=False)
            
            # Generate forecasts
            forecast_values = fitted.forecast(steps=periods)
            
            # Calculate prediction intervals using residual std
            residuals = series.values - fitted.fittedvalues
            residual_std = np.std(residuals)
            
            # Generate future periods
            last_period = series.index[-1]
            freq = pd.infer_freq(series.index) or 'MS'
            future_periods = pd.date_range(start=last_period, periods=periods + 1, freq=freq)[1:]
            
            forecasts = []
            for i, (period, value) in enumerate(zip(future_periods, forecast_values)):
                # Prediction interval widens with forecast horizon
                interval_width = residual_std * np.sqrt(i + 1) * 1.96
                forecasts.append({
                    "period": period.strftime("%Y-%m"),
                    "value": float(value),
                    "lower_bound": float(value - interval_width),
                    "upper_bound": float(value + interval_width),
                })
            
            summary = f"Forecast for next {periods} periods using exponential smoothing"
            if len(forecasts) > 0:
                first_forecast = forecasts[0]["value"]
                last_actual = float(series.values[-1])
                change = ((first_forecast - last_actual) / abs(last_actual)) * 100 if last_actual != 0 else 0
                summary += f" (next period: {first_forecast:.1f}, {change:+.1f}% vs current)"
            
            return {
                "summary": summary,
                "method": "Exponential Smoothing (Holt)",
                "forecasts": forecasts,
                "model_params": {
                    "alpha": float(fitted.params.get('smoothing_level', 0)),
                    "beta": float(fitted.params.get('smoothing_trend', 0)) if fitted.params.get('smoothing_trend') else None,
                }
            }
            
    except Exception as e:
        return {
            "summary": f"Forecasting failed: {str(e)[:100]}",
            "forecasts": [],
        }


def _run_statistical_tests(series: pd.Series) -> Optional[Dict[str, object]]:
    """Run statistical comparison tests on time series data."""
    if series is None or len(series) < 6:
        return None
    
    results = {}
    
    # Split into two halves for comparison (e.g., first half vs second half)
    mid = len(series) // 2
    first_half = series.values[:mid]
    second_half = series.values[mid:]
    
    # T-test: Are the two periods significantly different?
    try:
        t_stat, p_value = stats.ttest_ind(first_half, second_half)
        results["period_comparison"] = {
            "test": "Independent t-test",
            "comparison": "First half vs Second half",
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "summary": f"{'Significant' if p_value < 0.05 else 'No significant'} difference between periods (p={p_value:.4f})"
        }
    except Exception:
        pass
    
    # Test for stationarity (Augmented Dickey-Fuller test)
    if HAS_STATSMODELS:
        try:
            adf_result = adfuller(series.values, autolag='AIC')
            results["stationarity"] = {
                "test": "Augmented Dickey-Fuller",
                "adf_statistic": float(adf_result[0]),
                "p_value": float(adf_result[1]),
                "is_stationary": adf_result[1] < 0.05,
                "summary": f"Series is {'stationary' if adf_result[1] < 0.05 else 'non-stationary'} (p={adf_result[1]:.4f})"
            }
        except Exception:
            pass
    
    # Quartile-based comparison (ANOVA-like for segments)
    try:
        quartiles = pd.qcut(series.index.to_series(), q=4, labels=False, duplicates='drop')
        groups = [series.values[quartiles == i] for i in range(4) if len(series.values[quartiles == i]) > 0]
        
        if len(groups) >= 2:
            f_stat, p_value = stats.f_oneway(*groups)
            results["quarterly_variance"] = {
                "test": "One-way ANOVA",
                "comparison": "Across quarters",
                "f_statistic": float(f_stat),
                "p_value": float(p_value),
                "significant": p_value < 0.05,
                "summary": f"{'Significant' if p_value < 0.05 else 'No significant'} variance across quarters (p={p_value:.4f})"
            }
    except Exception:
        pass
    
    if not results:
        return None
    
    # Overall summary
    sig_tests = [v["summary"] for v in results.values() if "significant" in v.get("summary", "").lower()]
    overall = f"{len(sig_tests)} significant finding(s): " + "; ".join(sig_tests[:2]) if sig_tests else "No significant patterns detected"
    
    return {
        "summary": overall,
        "tests": results,
    }

