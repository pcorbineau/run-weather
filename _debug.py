import csv
import numpy as np

rows = []
with open(r'outputs/activity.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1))*np.cos(np.radians(lat2))*np.sin(dlon/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

km16_26 = []
cumul = 0.0
prev_lat, prev_lon = float(rows[0]['latitude']), float(rows[0]['longitude'])
for row in rows:
    lat, lon = float(row['latitude']), float(row['longitude'])
    d = haversine(prev_lat, prev_lon, lat, lon)
    cumul += d
    prev_lat, prev_lon = lat, lon
    if 16 <= cumul <= 26:
        km16_26.append(row)
    if cumul > 27:
        break

print(f'Points in km 16-26: {len(km16_26)}')
if not km16_26:
    print('No points found in km 16-26 range')
else:
    temps = [float(r['temperature']) for r in km16_26 if r['temperature']]
    apparents = [float(r['temperature_ressentie']) for r in km16_26 if r['temperature_ressentie']]
    altitudes = [float(r['altitude']) for r in km16_26 if r['altitude']]
    hrs = [float(r['fc']) for r in km16_26 if r['fc']]
    print(f'Temp range: {min(temps):.1f} - {max(temps):.1f}')
    print(f'Apparent temp range: {min(apparents):.1f} - {max(apparents):.1f}')
    print(f'Altitude range: {min(altitudes):.0f} - {max(altitudes):.0f} m')
    print(f'HR range: {min(hrs):.0f} - {max(hrs):.0f} bpm')
    step = max(1, len(km16_26) // 8)
    for i in range(0, len(km16_26), step):
        r = km16_26[i]
        felt = r.get('temperature_ressentie_soleil', 'N/A')
        print(f"  T={r['temperature']} AppT={r['temperature_ressentie']} Felt={felt} Alt={r['altitude']} FC={r['fc']} Hum={r['humidite']} H={r['heure'][11:16]}")
