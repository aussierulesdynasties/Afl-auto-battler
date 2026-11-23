"""Microsoft Global ML Building Footprints (CDLA Permissive 2.0) -> data/<g>/msbf.json: polygons in scene metres inside the near square."""
import sys, json, gzip, math
spec = json.load(open(sys.argv[1])); src = sys.argv[2]
lat0, lon0 = spec['lat'], spec['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540; N = spec['near_half_m']
out = []
for line in gzip.open(src, 'rt'):
    f = json.loads(line); ring = f['geometry']['coordinates'][0]
    P = [((lo - lon0) * KX, (la - lat0) * KY) for lo, la in ring]
    cx = sum(p[0] for p in P) / len(P); cy = sum(p[1] for p in P) / len(P)
    if abs(cx) < N and abs(cy) < N: out.append([[round(x, 2), round(y, 2)] for x, y in P])
json.dump(out, open('data/%s/msbf.json' % spec['name'], 'w')); print('MSBF', len(out))
