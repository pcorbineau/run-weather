from pathlib import Path
from zoneinfo import ZoneInfo

import folium
from folium.plugins import MousePosition
import numpy as np

from config import LOCAL_TIMEZONE
from models import Activity


VARIABLES = {
    "temperature": {
        "label": "Temperature (°C)",
        "getter": lambda ep: ep.weather.temperature_2m if ep.weather else None,
    },
    "apparent_temperature": {
        "label": "Temperature ressentie (°C)",
        "getter": lambda ep: ep.thermal.apparent_temperature if ep.thermal else None,
    },
    "heat_index": {
        "label": "Heat Index (°C)",
        "getter": lambda ep: ep.thermal.heat_index if ep.thermal else None,
    },
    "wbgt": {
        "label": "WBGT (°C)",
        "getter": lambda ep: ep.thermal.wbgt if ep.thermal else None,
    },
}


def _color_temp(val: float | None) -> str:
    if val is None:
        return "gray"
    if val < 20:
        return "green"
    if val < 25:
        return "#aadc00"
    if val < 30:
        return "orange"
    return "red"


def _downsample(points: list, max_points: int = 2000) -> list:
    if len(points) <= max_points:
        return points
    indices = np.linspace(0, len(points) - 1, max_points, dtype=int)
    return [points[i] for i in indices]


def generate_map(activity: Activity, output_path: Path) -> Path:
    local_tz = ZoneInfo(LOCAL_TIMEZONE)
    pts = _downsample(activity.points, max_points=2000)

    center_lat = pts[len(pts) // 2].track.latitude
    center_lon = pts[len(pts) // 2].track.longitude

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")

    for var_name, var_cfg in VARIABLES.items():
        fg = folium.FeatureGroup(name=var_cfg["label"], show=(var_name == "temperature"))

        coords = []
        colors = []
        tooltips = []

        for ep in pts:
            coords.append([ep.track.latitude, ep.track.longitude])
            val = var_cfg["getter"](ep)
            colors.append(_color_temp(val))
            tooltips.append(_tooltip(ep, val, var_cfg["label"], local_tz))

        for i in range(len(coords) - 1):
            folium.PolyLine(
                locations=[coords[i], coords[i + 1]],
                color=colors[i],
                weight=3,
                opacity=0.8,
                tooltip=tooltips[i],
            ).add_to(fg)

        fg.add_to(m)

    folium.LayerControl().add_to(m)
    MousePosition().add_to(m)

    m.save(str(output_path))
    return output_path


def _tooltip(ep, val: float | None, label: str, tz) -> str:
    parts = [f"{label}: {val:.1f}" if val is not None else f"{label}: N/A"]
    if ep.track.time:
        local_time = ep.track.time.astimezone(tz)
        parts.append(f"Heure: {local_time.strftime('%H:%M:%S')}")
    if ep.track.heart_rate is not None:
        parts.append(f"FC: {ep.track.heart_rate:.0f} bpm")
    if ep.pace_min_km is not None:
        parts.append(f"Allure: {ep.pace_min_km:.1f} min/km")
    if ep.track.elevation is not None:
        parts.append(f"Alt: {ep.track.elevation:.0f} m")
    return " | ".join(parts)
