import numpy as np
from scipy import stats

from models import Activity


def cardiac_drift(activity: Activity) -> dict:
    times = []
    hrs = []
    start = activity.points[0].track.time.timestamp() if activity.points else 0
    for ep in activity.points:
        if ep.track.heart_rate is not None and ep.track.time:
            t_elapsed = (ep.track.time.timestamp() - start) / 60.0
            times.append(t_elapsed)
            hrs.append(ep.track.heart_rate)

    if len(times) < 10:
        return {"slope": None, "intercept": None, "drift_bpm_per_hour": None}

    slope, intercept, r_value, p_value, std_err = stats.linregress(times, hrs)
    return {
        "slope": round(slope, 3),
        "intercept": round(intercept, 1),
        "drift_bpm_per_hour": round(slope * 60, 1),
        "r_squared": round(r_value**2, 3),
    }


def correlation_pace_temperature(activity: Activity) -> dict:
    pace_vals = []
    temp_vals = []
    for ep in activity.points:
        if ep.pace_min_km is not None and ep.weather is not None and ep.weather.temperature_2m is not None:
            pace_vals.append(ep.pace_min_km)
            temp_vals.append(ep.weather.temperature_2m)

    if len(pace_vals) < 10:
        return {"pearson": None, "p_value": None}

    r, p = stats.pearsonr(pace_vals, temp_vals)
    return {"pearson": round(r, 3), "p_value": round(p, 4)}


def correlation_hr_apparent_temp(activity: Activity) -> dict:
    hr_vals = []
    at_vals = []
    for ep in activity.points:
        if ep.track.heart_rate is not None and ep.thermal and ep.thermal.apparent_temperature is not None:
            hr_vals.append(ep.track.heart_rate)
            at_vals.append(ep.thermal.apparent_temperature)

    if len(hr_vals) < 10:
        return {"pearson": None, "p_value": None}

    r, p = stats.pearsonr(hr_vals, at_vals)
    return {"pearson": round(r, 3), "p_value": round(p, 4)}


def thermal_zones(activity: Activity) -> dict:
    points = activity.points
    thresholds = {"25": 0.0, "30": 0.0, "35": 0.0}

    for i, ep in enumerate(points):
        at = None
        if ep.thermal and ep.thermal.apparent_temperature is not None:
            at = ep.thermal.apparent_temperature
        elif ep.weather and ep.weather.apparent_temperature is not None:
            at = ep.weather.apparent_temperature
        else:
            continue

        duration = 1.0
        if i > 0 and points[i - 1].track.time and ep.track.time:
            dt = (ep.track.time - points[i - 1].track.time).total_seconds()
            if dt > 0:
                duration = dt

        for threshold_str in thresholds:
            threshold = float(threshold_str)
            if at > threshold:
                thresholds[threshold_str] += duration

    return {f"{t}": round(v, 0) for t, v in thresholds.items()}
