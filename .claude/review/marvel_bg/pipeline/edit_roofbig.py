"""Texture session 2026-11-20: roofs >= 1500 m2 and every tower roof use roof_far.png (24 m tile, ribs along the long axis);
small low-rise roofs keep corrugated. Water roughness 0.35."""
import json
P = 'scene.py'; s = open(P, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl); assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []]}",
    "    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []], 'big': [[], [], [], []]}")
rep("        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)\n        def ruv_(x, y): return ((x * ct + y * st) / 3.04, (-x * st + y * ct) / 3.04)\n",
    "        if not pitched and (cls == 'tower' or b.get('a', 0) >= spec.get('roof_big_m2', 1e12)): kind = 'big'\n"
    "        rs = spec.get('roof_big_m', 24.0) if kind == 'big' else 3.04\n"
    "        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)\n        def ruv_(x, y): return ((x * ct + y * st) / rs, (-x * st + y * ct) / rs)\n")
rep("os.path.join(HERE, 'tex', 'roof_%s.png' % ('corrugated' if kind == 'metal' else kind))",
    "os.path.join(HERE, 'tex', 'roof_%s.png' % {'metal': 'corrugated', 'big': 'far'}.get(kind, kind))")
open(P, 'w', newline='').write(s)
J = json.load(open('spec/marvel.json')); J['roof_big_m2'] = 1500; J['roof_big_m'] = 24.0; J['water_rough'] = 0.35
json.dump(J, open('spec/marvel.json', 'w'), indent=1); print('ok')
