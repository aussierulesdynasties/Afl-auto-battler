import sys
p = sys.argv[1]; s = open(p, newline='').read()
o = "uv += [(x / 104.0, y / 104.0) for x, y in _A]"
assert o in s
s = s.replace(o, "_E = np.diff(np.vstack([_A, _A[:1]]), axis=0); _e = _E[np.argmax(np.hypot(_E[:, 0], _E[:, 1]))]; _th = math.atan2(_e[1], _e[0]); _cs, _sn = math.cos(_th), math.sin(_th)\n    uv += [((x * _cs + y * _sn) / 15.6, (-x * _sn + y * _cs) / 16.0) for x, y in _A]   # bay rows run along the lot's longest side")
o2 = "mat_mul('park_asphalt', os.path.join(HERE, 'tex', 'road_asphalt_park.png'), 0.92, 1.0)"
assert o2 in s
s = s.replace(o2, "mat_mul('park_bays', os.path.join(HERE, 'tex', 'mt', 'park_bays.png'), 0.92, 1.0)")
if 'import math' not in s: s = 'import math\n' + s
open(p, 'w', newline='').write(s); print('ok')
