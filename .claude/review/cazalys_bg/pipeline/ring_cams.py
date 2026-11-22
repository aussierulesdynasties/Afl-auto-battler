"""Ring cameras placed outside the stadium GLB: radius = farthest model vertex within +-20 deg of the view direction + 15 m.
python -E ring_cams.py ground/cazalys.glb out/cazalys/job_ring.json"""
import sys, struct, json, math, numpy as np
f = open(sys.argv[1], 'rb'); f.read(12); n, _ = struct.unpack('<II', f.read(8)); j = json.loads(f.read(n)); bl, _ = struct.unpack('<II', f.read(8)); B = f.read(bl)
P = []
for m in j['meshes']:
    for p in m['primitives']:
        a = j['accessors'][p['attributes']['POSITION']]; v = j['bufferViews'][a['bufferView']]
        o = v.get('byteOffset', 0) + a.get('byteOffset', 0); s = v.get('byteStride', 12)
        P.append(np.frombuffer(B, np.uint8, count=s * a['count'], offset=o).reshape(-1, s)[:, :12].copy().view(np.float32))
P = np.vstack(P); x, y = P[:, 0], -P[:, 2]; ang = np.degrees(np.arctan2(y, x)) % 360; r = np.hypot(x, y)
J = json.load(open(sys.argv[2]))
for vw in J['views']:
    cx, cy, cz = vw['cam']; d = math.degrees(math.atan2(cy, cx)) % 360
    rmax = float(r[np.abs((ang - d + 180) % 360 - 180) < 20].max()); R = max(math.hypot(cx, cy), rmax + 15)
    ux, uy = math.cos(math.radians(d)), math.sin(math.radians(d))
    vw['cam'] = [round(R * ux, 2), round(R * uy, 2), cz]; vw['look'] = [round((R + 100) * ux, 2), round((R + 100) * uy, 2), vw['look'][2]]
    print(vw['name'], 'model', round(float(rmax), 1), 'cam', round(R, 1))
json.dump(J, open(sys.argv[2], 'w'))
