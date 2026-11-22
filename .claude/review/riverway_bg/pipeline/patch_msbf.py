s = open('prep.py', encoding='utf-8', newline='').read()
anchor = "json.dump(BLD, open(os.path.join(OUT, 'buildings.json'), 'w'))"
add = """_MS = os.path.join(D, 'msbf.json')
if os.path.exists(_MS):   # Microsoft ML footprints (CDLA-P-2.0) fill buildings OSM lacks; height from its type, like OSM
    from matplotlib.path import Path as _Pa
    _op = [(_Pa(b['p']), np.min(b['p'], 0) - 2, np.max(b['p'], 0) + 2) for b in BLD]; _n = 0
    for pts in json.load(open(_MS)):
        pts = [tuple(p) for p in pts]; pts = pts[:-1] if pts[0] == pts[-1] else pts
        cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
        if math.hypot(cx, cy) < skip_r: continue
        if any(lo[0] < cx < hi[0] and lo[1] < cy < hi[1] and pa.contains_point((cx, cy), radius=2) for pa, lo, hi in _op): continue
        if area(pts) < 0: pts = pts[::-1]
        A = abs(area(pts))
        if A < 12: continue
        cls = 'house' if A < 350 else 'block'; h = LV['house'] if cls == 'house' else LV['*']
        BLD.append(dict(p=[[round(x, 2), round(y, 2)] for x, y in pts], h=round(h, 1), c=cls, ms=1,
                        roof=int(rng.integers(0, len(PAL['roofs_' + ('house' if cls == 'house' else 'flat')]))),
                        wall=int(rng.integers(0, len(PAL['walls_' + cls])))))
        _n += 1
    print('msbf added', _n)
"""
assert anchor in s; s = s.replace(anchor, add + anchor, 1); open('prep.py', 'w', encoding='utf-8', newline='').write(s)
