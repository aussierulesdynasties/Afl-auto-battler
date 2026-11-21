# Move a ground's origin to the fitted fence-ellipse centre: python3 kit/recentre.py tools/grounds/<slug> x0 y0 a1 a2 rot
# Shifts lat/lon by (x0, y0) metres, sets 'fence' to [0, 0, a1, a2, rot] and refetches work/sat.png.
import sys, os, json, math, subprocess
G = os.path.abspath(sys.argv[1]); SLUG = os.path.basename(G); p = os.path.join(G, 'model', SLUG + '.json'); D = json.load(open(p))
x0, y0, a1, a2, rot = map(float, sys.argv[2:7]); q = math.radians(D['lat'])
MLAT = 111132.92 - 559.82 * math.cos(2 * q) + 1.175 * math.cos(4 * q); MLON = 111412.84 * math.cos(q) - 93.5 * math.cos(3 * q)
D['lat'] = round(D['lat'] + y0 / MLAT, 7); D['lon'] = round(D['lon'] + x0 / MLON, 7); D['fence'] = [0, 0, round(a1, 2), round(a2, 2), round(rot, 2)]
json.dump(D, open(p, 'w'), indent=1); subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'sat.py'), G], check=True)
