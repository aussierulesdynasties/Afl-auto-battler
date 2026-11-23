# Paving cut line = OSM stadium building outline (way 4385777) + 1 m, not the roof/arch footprint.
# The roof+arch footprint (142-171 m) left a grass ring between the wall and the paving; the real forecourt paves to the wall.
import json, math, numpy as np
lat0, lon0 = -33.847086, 151.063400; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
E = json.load(open('data/accor/osm.json', encoding='utf-8'))['elements']
w = [e for e in E if e['id'] == 4385777 and e['type'] == 'way'][0]
P = np.array([((g['lon'] - lon0) * KX, (g['lat'] - lat0) * KY) for g in w['geometry']])
D = np.vstack([a + (b - a) * t for a, b in zip(P[:-1], P[1:]) for t in np.linspace(0, 1, 40, endpoint=False)])
ang = (np.degrees(np.arctan2(D[:, 1], D[:, 0])) % 360) // 2; r = np.hypot(*D.T)
R = np.array([r[ang == k].max() if (ang == k).any() else 0 for k in range(180)]) + 1
json.dump([round(float(x), 2) for x in R], open('data/accor/prep/wall.json', 'w'))
print('WALL', R.min().round(1), R.max().round(1))
