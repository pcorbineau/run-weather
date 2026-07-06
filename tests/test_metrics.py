from models import TrackPoint, EnhancedPoint, HourlyWeather
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
    assert 20 < wbgt < 35


def test_apparent_from_provider():
    w = HourlyWeather(time=None, temperature_2m=25.0, relative_humidity_2m=50.0, wind_speed_10m=10.0, apparent_temperature=30.0)
    tp = TrackPoint(time=None, latitude=0.0, longitude=0.0)
    ep = EnhancedPoint(track=tp, weather=w)
    th = compute_thermal_metrics(ep)
    assert th.apparent_temperature == 30.0
