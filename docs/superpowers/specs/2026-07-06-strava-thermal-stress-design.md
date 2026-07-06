# Analyse du stress thermique à partir d'activités Strava

## Objectif

Application Python analysant les conditions thermiques rencontrées pendant une activité sportive (course à pied, trail, randonnée, vélo) à partir d'un fichier GPX exporté Strava. Estime la température ressentie et le stress thermique sans capteur externe.

## Architecture

Pipeline linéaire modulaire :

```
Fichier GPX → GPXLoader → WeatherService → MetricsEngine → Charts → Map → Report
```

### Arborescence

```
project/
├── main.py                 # CLI orchestrateur (argparse)
├── config.py               # Chemins, clés API, paramètres
├── models.py               # Dataclasses : TrackPoint, HourlyWeather, Activity, ThermalMetrics
├── loaders/
│   ├── base.py             # Abstract ActivityLoader
│   └── gpx_loader.py       # GPX → list[TrackPoint]
├── strava/
│   ├── auth.py             # OAuth token management (futur)
│   └── api.py              # Strava API client (futur)
├── weather/
│   ├── base.py             # Abstract WeatherProvider
│   ├── open_meteo.py       # Open-Meteo Archive API
│   └── era5.py             # ERA5 (futur)
├── cache.py                # diskcache wrapper
├── metrics.py              # Indices thermiques purs
├── analysis.py             # Corrélations, dérive cardiaque, zones thermiques
├── charts.py               # Matplotlib (8 graphiques)
├── maps.py                 # Folium (carte interactive colorée)
├── report.py               # Jinja2 HTML + CSV export
├── outputs/                # Rapports générés
├── cache/                  # Cache disque météo
└── tests/
```

## Sources de données

### Activités (v1)

- **GPX** : via `gpxpy`, extraction lat/lon/altitude/time/FC/cadence
- **FIT** : via `fitparse` (v2)
- **API Strava** : OAuth avec tokens existants (v2)

### Météo

**Stratégie** : une requête Open-Meteo Archive par jour d'activité + interpolation temporelle linéaire pour chaque point GPS.

- API : `https://archive-api.open-meteo.com/v1/archive`
- Variables : température (2m), humidité relative, vitesse vent (10m), rafales, pression, nébulosité, rayonnement solaire, point de rosée, température apparente
- Cache : `diskcache` indexé par `(date, lat_rounded_2dec, lon_rounded_2dec)`, TTL 30 jours
- Interface `WeatherProvider` permettant d'ajouter ERA5 plus tard

## Calculs thermiques

Calculés pour chaque point via `metrics.py` :

| Indice | Source | Condition |
|--------|--------|-----------|
| Température apparente | Steadman (1994) | toujours |
| Heat Index | Rothfusz (NOAA) | T > 27°C, HR > 40% |
| Wind Chill | NWS | T ≤ 10°C, vent > 4.8 km/h |
| Humidex | Environnement Canada | toujours |
| WBGT simplifié | 0.567·T + 0.393·HR + 3.94 | toujours |

## Analyse (`analysis.py`)

- Dérive cardiaque : régression linéaire FC(t), pente
- Corrélation allure↔température : Pearson
- Corrélation FC↔température ressentie : Pearson
- Temps passé par zone thermique : cumul durées des points > 25°C, 30°C, 35°C ressentie

## Visualisations

### Graphiques Matplotlib (8 fichiers .png)

1. Température vs temps
2. Température ressentie vs temps
3. Humidité vs temps
4. FC vs temps
5. Allure vs temps
6. Altitude vs temps
7. Température + FC (double axe Y)
8. Température ressentie + allure (double axe Y)

### Carte Folium

- Parcours coloré par variable (température, ressentie, HI, WBGT)
- Layer control pour changer la variable
- Popup au survol : heure, T°, T° ressentie, FC, allure, altitude
- Sauvegardée dans `outputs/`

## Rapports

### CSV

Une ligne par point : heure, lat, lon, altitude, température, humidité, vent, température ressentie, HI, WBGT, FC, allure

### HTML (Jinja2, tout inline)

- Résumé de l'activité (nom, date, durée, distance, D+, D-)
- Statistiques météo (min/max/moy T°, humidité moyenne, vent moyen, WBGT max)
- Tableau des zones thermiques avec durées
- Graphiques intégrés en base64
- Carte interactive intégrée
- Tableau des corrélations

## Tests

- Unitaires pour chaque module (pytest)
- Mock de l'API météo
- Fichier GPX de test dans `tests/fixtures/`

## Contraintes techniques

- Python 3.12+
- Typage strict (type hints)
- Séparation acquisition / calculs / visualisation / rapport
- Architecture extensible (interface `WeatherProvider`, `ActivityLoader`)
