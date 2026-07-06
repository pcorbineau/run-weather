import base64
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import jinja2
import pandas as pd

from config import LOCAL_TIMEZONE
from models import Activity


REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rapport thermique - {{ name }}</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1100px; margin: 0 auto; padding: 20px; color: #333; }
h1, h2, h3 { color: #1a1a2e; }
.summary { background: #f0f4f8; padding: 20px; border-radius: 8px; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin: 16px 0; }
.summary-item { text-align: center; }
.summary-item .value { font-size: 1.8em; font-weight: bold; color: #1a1a2e; }
.summary-item .label { font-size: 0.85em; color: #666; }
table { width: 100%; border-collapse: collapse; margin: 16px 0; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background: #f0f4f8; }
.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.chart-grid img { width: 100%; border-radius: 6px; border: 1px solid #e0e0e0; }
.map-container { width: 100%; height: 500px; border: 1px solid #e0e0e0; border-radius: 8px; margin: 16px 0; }
.map-container iframe { width: 100%; height: 100%; border: none; border-radius: 8px; }
@media (max-width: 700px) { .chart-grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<h1>{{ name }}</h1>
<p><strong>Date:</strong> {{ date }} &middot; <strong>Type:</strong> {{ sport_type }}</p>

<div class="summary">
<div class="summary-item"><div class="value">{{ "%.1f"|format(distance_km) }}</div><div class="label">Distance (km)</div></div>
<div class="summary-item"><div class="value">{{ duration_str }}</div><div class="label">Durée</div></div>
<div class="summary-item"><div class="value">{{ "%.0f"|format(elevation_gain) }}</div><div class="label">D+ (m)</div></div>
<div class="summary-item"><div class="value">{{ "%.0f"|format(elevation_loss) }}</div><div class="label">D- (m)</div></div>
</div>

<h2>Statistiques météo</h2>
<table>
<tr><th>Variable</th><th>Min</th><th>Moy</th><th>Max</th></tr>
{% for var, vals in weather_stats.items() %}
<tr><td>{{ var }}</td><td>{{ vals.min }}</td><td>{{ vals.avg }}</td><td>{{ vals.max }}</td></tr>
{% endfor %}
</table>

<h2>Zones thermiques (température ressentie)</h2>
<table>
<tr><th>Seuil</th><th>Temps passé</th></tr>
{% for zone, seconds in thermal_zones.items() %}
<tr><td>&gt; {{ zone }}°C</td><td>{{ "%d min"|format(seconds // 60) }}</td></tr>
{% endfor %}
</table>

<h2>Corrélations</h2>
<table>
<tr><th>Relation</th><th>Coefficient (Pearson)</th></tr>
{% for label, val in correlations.items() %}
<tr><td>{{ label }}</td><td>{{ val if val is not none else "N/A" }}</td></tr>
{% endfor %}
</table>

<h2>Graphiques</h2>
<div class="chart-grid">
{% for chart in charts %}
<img src="data:image/png;base64,{{ chart.data }}" alt="{{ chart.label }}">
{% endfor %}
</div>

<h2>Carte interactive</h2>
<div class="map-container">{{ map_html | safe }}</div>

<p style="text-align:center;color:#999;font-size:0.85em;margin-top:40px;">
Généré par run-weather le {{ generation_time }}
</p>
</body>
</html>"""


def generate_csv(activity: Activity, path: Path) -> Path:
    local_tz = ZoneInfo(LOCAL_TIMEZONE)
    rows = []
    for ep in activity.points:
        t = ep.track
        w = ep.weather
        th = ep.thermal
        local_time = t.time.astimezone(local_tz) if t.time else None
        rows.append({
            "heure": local_time.isoformat() if local_time else "",
            "latitude": t.latitude,
            "longitude": t.longitude,
            "altitude": t.elevation or "",
            "temperature": w.temperature_2m if w else "",
            "humidite": w.relative_humidity_2m if w else "",
            "vent": w.wind_speed_10m if w else "",
            "temperature_ressentie": th.apparent_temperature if th else "",
            "heat_index": th.heat_index if th else "",
            "wbgt": th.wbgt if th else "",
            "fc": t.heart_rate or "",
            "allure": ep.pace_min_km or "",
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return path


def generate_html_report(activity: Activity, charts: list[Path], map_path: Path, output_path: Path) -> Path:
    template = jinja2.Template(REPORT_TEMPLATE)

    weather_stats = _weather_stats(activity)
    thermal_zones_data = _thermal_zones_data(activity)
    correlations = _correlations_data(activity)

    chart_b64 = []
    for ch in charts:
        with open(ch, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        chart_b64.append({"label": ch.stem.replace("_", " ").title(), "data": b64})

    map_html = ""
    if map_path and map_path.exists():
        map_html = map_path.read_text(encoding="utf-8")

    duration_sec = activity.duration
    hours, remainder = divmod(int(duration_sec), 3600)
    minutes, _ = divmod(remainder, 60)
    duration_str = f"{hours}h{minutes:02d}" if hours > 0 else f"{minutes} min"

    local_tz = ZoneInfo(LOCAL_TIMEZONE)
    local_start = activity.start_time.astimezone(local_tz) if activity.start_time else None

    html = template.render(
        name=activity.name,
        date=local_start.strftime("%d/%m/%Y %H:%M") if local_start else "",
        sport_type=activity.sport_type,
        distance_km=activity.distance_km,
        duration_str=duration_str,
        elevation_gain=activity.elevation_gain,
        elevation_loss=activity.elevation_loss,
        weather_stats=weather_stats,
        thermal_zones=thermal_zones_data,
        correlations=correlations,
        charts=chart_b64,
        map_html=map_html,
        generation_time=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )

    output_path.write_text(html, encoding="utf-8")
    return output_path


def _weather_stats(activity: Activity) -> dict:
    stats = {
        "Température (°C)": [],
        "Humidité (%)": [],
        "Vent (km/h)": [],
        "Température apparente (°C)": [],
    }
    for ep in activity.points:
        if ep.weather:
            stats["Température (°C)"].append(ep.weather.temperature_2m)
            stats["Humidité (%)"].append(ep.weather.relative_humidity_2m)
            stats["Vent (km/h)"].append(ep.weather.wind_speed_10m)
        if ep.thermal and ep.thermal.apparent_temperature is not None:
            stats["Température apparente (°C)"].append(ep.thermal.apparent_temperature)

    result = {}
    for label, vals in stats.items():
        if vals:
            result[label] = {
                "min": f"{min(vals):.1f}",
                "avg": f"{sum(vals)/len(vals):.1f}",
                "max": f"{max(vals):.1f}",
            }
        else:
            result[label] = {"min": "-", "avg": "-", "max": "-"}
    return result


def _thermal_zones_data(activity: Activity) -> dict:
    from analysis import thermal_zones
    return thermal_zones(activity)


def _correlations_data(activity: Activity) -> dict:
    from analysis import correlation_pace_temperature, correlation_hr_apparent_temp, cardiac_drift

    pace_temp = correlation_pace_temperature(activity)
    hr_at = correlation_hr_apparent_temp(activity)
    drift = cardiac_drift(activity)

    return {
        "Allure ↔ Température": pace_temp.get("pearson"),
        "FC ↔ Température ressentie": hr_at.get("pearson"),
        "Dérive cardiaque (bpm/h)": drift.get("drift_bpm_per_hour"),
    }
