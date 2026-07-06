from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from models import Activity


def generate_charts(activity: Activity, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = []

    points = activity.points
    times = [ep.track.time for ep in points]
    temps = [ep.weather.temperature_2m if ep.weather else None for ep in points]
    apparents = [ep.thermal.apparent_temperature if ep.thermal else None for ep in points]
    hums = [ep.weather.relative_humidity_2m if ep.weather else None for ep in points]
    hrs = [ep.track.heart_rate for ep in points]
    paces = [ep.pace_min_km for ep in points]
    elevs = [ep.track.elevation for ep in points]

    charts = [
        ("temperature_vs_time", "Temperature (°C)", temps),
        ("apparent_temp_vs_time", "Temperature ressentie (°C)", apparents),
        ("humidity_vs_time", "Humidite (%)", hums),
        ("heart_rate_vs_time", "Frequence cardiaque (bpm)", hrs),
        ("pace_vs_time", "Allure (min/km)", paces),
        ("elevation_vs_time", "Altitude (m)", elevs),
    ]

    for name, ylabel, values in charts:
        xt, yv = _clean_pairs(times, values)
        if not yv:
            continue
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(xt, yv, linewidth=0.8)
        ax.set_ylabel(ylabel)
        ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
        fig.autofmt_xdate()
        path = output_dir / f"{name}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        files.append(path)
        plt.close(fig)

    _dual_chart(times, temps, apparents, "Temperature (°C)", "Temp. ressentie (°C)",
                output_dir / "temperature_comparison.png", files)
    _dual_chart(times, hrs, paces, "FC (bpm)", "Allure (min/km)",
                output_dir / "hr_pace_comparison.png", files)

    return files


def _clean_pairs(times: list, values: list):
    xt = []
    yv = []
    for t, v in zip(times, values):
        if v is not None:
            xt.append(t)
            yv.append(v)
    return xt, yv


def _dual_chart(times, vals1, vals2, label1, label2, path: Path, files: list):
    xt1, y1 = _clean_pairs(times, vals1)
    xt2, y2 = _clean_pairs(times, vals2)
    if not y1 or not y2:
        return
    fig, ax1 = plt.subplots(figsize=(12, 4))
    ax1.plot(xt1, y1, "b-", linewidth=0.8, label=label1)
    ax1.set_ylabel(label1, color="b")
    ax2 = ax1.twinx()
    ax2.plot(xt2, y2, "r-", linewidth=0.8, label=label2)
    ax2.set_ylabel(label2, color="r")
    ax1.xaxis.set_major_formatter(DateFormatter("%H:%M"))
    fig.autofmt_xdate()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    files.append(path)
    plt.close(fig)
