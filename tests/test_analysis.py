from datetime import datetime, timezone
from models import TrackPoint, EnhancedPoint, Activity, HourlyWeather, ThermalMetrics
from analysis import cardiac_drift, correlation_hr_apparent_temp


def _make_activity_with_hr():
    t0 = datetime(2026, 7, 4, 11, 0, 0, tzinfo=timezone.utc)
    points = []
    for i in range(20):
        t = TrackPoint(
            time=datetime(2026, 7, 4, 11, i, 0, tzinfo=timezone.utc),
            latitude=43.0, longitude=1.0, heart_rate=140.0 + i * 0.5,
        )
        points.append(EnhancedPoint(track=t))
    return Activity(name="Test", sport_type="running", start_time=t0, points=points)


def test_cardiac_drift():
    activity = _make_activity_with_hr()
    drift = cardiac_drift(activity)
    assert drift["slope"] is not None
    assert drift["drift_bpm_per_hour"] is not None


def test_correlation_no_data():
    t0 = datetime(2026, 7, 4, 11, 0, 0, tzinfo=timezone.utc)
    p = TrackPoint(time=t0, latitude=43.0, longitude=1.0)
    activity = Activity(name="Test", sport_type="running", start_time=t0, points=[EnhancedPoint(track=p)])
    corr = correlation_hr_apparent_temp(activity)
    assert corr["pearson"] is None
