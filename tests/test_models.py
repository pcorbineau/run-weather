from datetime import datetime, timezone
from models import TrackPoint, EnhancedPoint, Activity, haversine


def test_haversine_same_point():
    d = haversine(43.0, 1.0, 43.0, 1.0)
    assert d == 0.0


def test_haversine_known_distance():
    d = haversine(48.8566, 2.3522, 48.8570, 2.3522)
    assert 0.03 < d < 0.05


def test_activity_distance():
    t0 = datetime(2026, 7, 4, 11, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 7, 4, 11, 1, 0, tzinfo=timezone.utc)
    p0 = TrackPoint(time=t0, latitude=43.0, longitude=1.0)
    p1 = TrackPoint(time=t1, latitude=43.001, longitude=1.001)
    activity = Activity(
        name="Test", sport_type="running", start_time=t0,
        points=[EnhancedPoint(track=p0), EnhancedPoint(track=p1)],
    )
    assert activity.distance_km > 0
    assert activity.duration == 60.0
