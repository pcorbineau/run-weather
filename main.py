import argparse
import sys
from pathlib import Path

import config
from loaders.gpx_loader import GPXLoader
from weather.open_meteo import OpenMeteoProvider
from weather.service import WeatherService
from cache import WeatherCache
from metrics import compute_all_metrics, compute_pace
from analysis import cardiac_drift, correlation_pace_temperature, correlation_hr_apparent_temp, thermal_zones
from charts import generate_charts
from maps import generate_map
from report import generate_csv, generate_html_report


def main():
    parser = argparse.ArgumentParser(description="Analyse du stress thermique d'une activité Strava")
    parser.add_argument("file", help="Chemin vers le fichier GPX")
    parser.add_argument("--output", "-o", default=None, help="Dossier de sortie (défaut: outputs/)")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Erreur: fichier introuvable: {file_path}")
        sys.exit(1)

    output_dir = Path(args.output) if args.output else config.OUTPUTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load activity
    print("Chargement de l'activité...")
    loader = GPXLoader()
    activity = loader.load(str(file_path))
    print(f"  {activity.name} — {len(activity.points)} points")

    # 2. Compute pace
    print("Calcul des allures...")
    compute_pace(activity.points)

    # 3. Fetch weather
    print("Récupération des données météo...")
    cache = WeatherCache()
    provider = OpenMeteoProvider()
    weather_service = WeatherService(provider, cache)
    activity = weather_service.enrich(activity)
    cache.close()
    print("  Météo récupérée")

    # 4. Compute metrics
    print("Calcul des indices thermiques...")
    compute_all_metrics(activity.points)

    # 5. Analysis
    print("Analyse...")
    drift = cardiac_drift(activity)
    corr_pace_temp = correlation_pace_temperature(activity)
    corr_hr_at = correlation_hr_apparent_temp(activity)
    zones = thermal_zones(activity)
    print(f"  Derive cardiaque: {drift.get('drift_bpm_per_hour', 'N/A')} bpm/h")
    print(f"  Correlation allure<->temperature: {corr_pace_temp.get('pearson', 'N/A')}")

    # 6. Charts
    print("Génération des graphiques...")
    chart_files = generate_charts(activity, output_dir)

    # 7. Map
    print("Génération de la carte...")
    map_path = output_dir / "activity_map.html"
    generate_map(activity, map_path)

    # 8. CSV
    print("Export CSV...")
    csv_path = output_dir / "activity.csv"
    generate_csv(activity, csv_path)

    # 9. HTML report
    print("Génération du rapport HTML...")
    report_path = output_dir / "report.html"
    generate_html_report(activity, chart_files, map_path, report_path)

    print(f"\nTerminé. Résultats dans: {output_dir.resolve()}")
    print(f"  Rapport: {report_path}")
    print(f"  CSV:     {csv_path}")
    print(f"  Carte:   {map_path}")


if __name__ == "__main__":
    main()
