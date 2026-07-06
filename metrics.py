import numpy as np

from models import EnhancedPoint, ThermalMetrics


def _vp(T: float, HR: float) -> float:
    return (HR / 100.0) * 6.105 * np.exp(17.27 * T / (237.7 + T))


def _heat_index(T: float, HR: float) -> float | None:
    if T < 27 or HR < 40:
        return None
    hi = (
        -8.78469475556
        + 1.61139411 * T
        + 2.33854883889 * HR
        - 0.14611605 * T * HR
        - 0.012308094 * T**2
        - 0.0164248277778 * HR**2
        + 0.002211732 * T**2 * HR
        + 0.00072546 * T * HR**2
        - 0.000003582 * T**2 * HR**2
    )
    return round(hi, 1)


def _wind_chill(T: float, WS: float) -> float | None:
    if T > 10 or WS < 4.8:
        return None
    wc = 13.12 + 0.6215 * T - 11.37 * (WS * 3.6) ** 0.16 + 0.3965 * T * (WS * 3.6) ** 0.16
    return round(wc, 1)


def _humidex(T: float, HR: float) -> float:
    e = _vp(T, HR)
    hx = T + 0.5555 * (e - 10)
    return round(hx, 1)


def _wbgt_simple(T: float, HR: float) -> float:
    e = _vp(T, HR)
    wbgt = 0.567 * T + 0.393 * e + 3.94
    return round(wbgt, 1)


def _apparent_temperature(T: float, HR: float, WS: float) -> float:
    e = _vp(T, HR)
    Ta = T + 0.33 * e - 0.70 * WS - 4.00
    return round(Ta, 1)


def _wind_shelter_factor(elevation: float | None, local_terrain_range: float | None = None) -> float:
    base = (1.5 / 10.0) ** 0.14
    if elevation is not None and elevation > 300:
        base *= max(0.45, 1.0 - 0.00012 * (elevation - 300))
    if local_terrain_range is not None and local_terrain_range > 100:
        base *= max(0.3, 1.0 - 0.0008 * (local_terrain_range - 100))
    return base


def _felt_temperature(T: float, HR: float, WS: float, SR: float | None,
                      elevation: float | None = None, terrain_range: float | None = None) -> float:
    e = _vp(T, HR)
    shelter = _wind_shelter_factor(elevation, terrain_range)
    ws_body = WS * shelter
    rad = SR if SR is not None else 0.0

    solar_factor = 0.012
    if elevation is not None and elevation > 300:
        solar_factor = min(0.022, 0.012 + 0.0025 * ((elevation - 300) / 1000))

    ft = T + 0.33 * e - 0.70 * ws_body + solar_factor * rad - 4.00
    return round(ft, 1)


def compute_thermal_metrics(ep: EnhancedPoint, terrain_range: float | None = None) -> ThermalMetrics:
    w = ep.weather
    if w is None:
        return ThermalMetrics()

    T = w.temperature_2m
    HR = w.relative_humidity_2m
    WS = w.wind_speed_10m
    SR = w.shortwave_radiation
    elev = ep.track.elevation

    apparent = w.apparent_temperature if w.apparent_temperature is not None else _apparent_temperature(T, HR, WS)
    felt = _felt_temperature(T, HR, WS, SR, elev, terrain_range)
    hi = _heat_index(T, HR)
    wc = _wind_chill(T, WS)
    hx = _humidex(T, HR)
    wbgt_val = _wbgt_simple(T, HR)

    return ThermalMetrics(
        apparent_temperature=apparent,
        felt_temperature=felt,
        heat_index=hi,
        wind_chill=wc,
        humidex=hx,
        wbgt=wbgt_val,
    )


def _terrain_ranges(points: list[EnhancedPoint], window: int = 60) -> list[float | None]:
    eles = [ep.track.elevation for ep in points]
    ranges = []
    for i in range(len(points)):
        start = max(0, i - window)
        end = min(len(points), i + window + 1)
        window_eles = [e for e in eles[start:end] if e is not None]
        if len(window_eles) >= 3:
            ranges.append(max(window_eles) - min(window_eles))
        else:
            ranges.append(None)
    return ranges


def compute_all_metrics(points: list[EnhancedPoint]) -> list[EnhancedPoint]:
    terrain_ranges = _terrain_ranges(points)
    for ep, tr in zip(points, terrain_ranges):
        ep.thermal = compute_thermal_metrics(ep, tr)
    return points


def compute_pace(points: list[EnhancedPoint]) -> list[EnhancedPoint]:
    for i in range(1, len(points)):
        p1 = points[i - 1].track
        p2 = points[i].track
        dt = (p2.time - p1.time).total_seconds()
        if dt <= 0:
            continue
        from models import haversine
        d = haversine(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
        if d > 0:
            points[i].pace_min_km = (dt / 60.0) / d
    return points
