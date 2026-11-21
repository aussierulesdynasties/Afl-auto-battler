"""Marvel rejection 2026-11-20 (plan session relaying the director): buildings carry their OSM kind/material/colour so
scene.py can give each its own facade; platforms are exported; yard tracks get their own darker ballast colour."""
P = 'prep.py'; s = open(P, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl); assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("    if shed: BLD[-1]['rc'] = spec['shed_roof']\n",
    "    if shed: BLD[-1]['rc'] = spec['shed_roof']\n"
    "    BLD[-1]['k'] = kind\n"
    "    for _tk, _bk in (('building:material', 'mat'), ('building:colour', 'col'), ('railway', 'rw'), ('amenity', 'am'), ('parking', 'pk')):\n"
    "        if _tk in t: BLD[-1][_bk] = t[_tk]\n")
rep("json.dump(RL, open(os.path.join(OUT, 'rails.json'), 'w'))\n",
    "json.dump(RL, open(os.path.join(OUT, 'rails.json'), 'w'))\n"
    "PF = []   # railway platforms (closed ways): raised concrete slabs in scene.py\n"
    "for el in js:\n"
    "    t = el.get('tags', {})\n"
    "    if el['type'] != 'way' or t.get('railway') != 'platform': continue\n"
    "    pts = ring(el)\n"
    "    if len(pts) > 3 and pts[0] == pts[-1] and all(abs(x) < NEAR and abs(y) < NEAR for x, y in pts):\n"
    "        PF.append([[round(x, 2), round(y, 2)] for x, y in pts[:-1]])\n"
    "json.dump(PF, open(os.path.join(OUT, 'platforms.json'), 'w')); print('platforms', len(PF))\n")
rep("dr.line(P(pts), fill=tuple(PAL['ballast']), width=max(1, int(6 / PX)))",
    "dr.line(P(pts), fill=tuple(PAL.get('ballast_track', PAL['ballast'])), width=max(1, int(spec.get('ballast_track_m', 6) / PX)))")
open(P, 'w', newline='').write(s); print('ok')
