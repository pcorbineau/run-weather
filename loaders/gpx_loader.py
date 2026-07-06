from datetime import timezone, datetime

import gpxpy

from models import Activity, TrackPoint, EnhancedPoint
from loaders.base import ActivityLoader


class GPXLoader(ActivityLoader):
    def load(self, path: str) -> Activity:
        with open(path, "r", encoding="utf-8") as f:
            gpx = gpxpy.parse(f)

        track = gpx.tracks[0]
        segment = track.segments[0]

        points: list[TrackPoint] = []
        for pt in segment.points:
            hr = None
            cad = None
            if pt.extensions:
                for ext in pt.extensions:
                    for child in ext.iter():
                        tag = child.tag.split("}")[-1]
                        if tag == "hr" and child.text:
                            hr = float(child.text)
                        elif tag == "cad" and child.text:
                            cad = float(child.text)

            if pt.time:
                time = pt.time.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
            else:
                time = None

            tp = TrackPoint(
                time=time,
                latitude=pt.latitude,
                longitude=pt.longitude,
                elevation=pt.elevation,
                heart_rate=hr,
                cadence=cad,
            )
            points.append(tp)

        points.sort(key=lambda p: p.time)

        enhanced = []
        for i, p in enumerate(points):
            pace = None
            if i > 0 and p.time and points[i - 1].time:
                dt = (p.time - points[i - 1].time).total_seconds()
                dlat = p.latitude - points[i - 1].latitude
                dlon = p.longitude - points[i - 1].longitude
                if dt > 0 and (dlat != 0 or dlon != 0):
                    pace = dt / 60.0
            enhanced.append(EnhancedPoint(track=p, pace_min_km=pace))

        name = track.name or gpx.name or "Unknown"
        sport_type = track.type or "other"
        start_time = points[0].time if points else datetime.now(timezone.utc)

        return Activity(name=name, sport_type=sport_type, start_time=start_time, points=enhanced)
