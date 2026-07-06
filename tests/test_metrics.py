from models import TrackPoint, EnhancedPoint
from metrics import compute_thermal_metrics, _heat_index, _wind_chill, _wbgt_simple


def test_heat_index_hot_humid():
    hi = _heat_index(30.0, 70.0)
    assert hi is not None
    assert hi > 30


def test_heat_index_cold():
    hi = _heat_index(15.0, 50.0)
    assert hi is None


def test_wind_chill_cold_windy():
    wc = _wind_chill(-5.0, 20.0)
    assert wc is not None
    assert wc < -5


def test_wind_chill_warm():
    wc = _wind_chill(15.0, 20.0)
    assert wc is None


def test_wbgt_simple():
    wbgt = _wbgt_simple(30.0, 60.0)
    assert 25 < wbgt < 45
