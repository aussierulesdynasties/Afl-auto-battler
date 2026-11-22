s = open('accor_towers.py', newline='').read()
a = s.index("_T = json.load("); b = s.index("_TV, _TF = [], []")
s = s[:a] + """# 19 towers, curated one by one on the aerial (_towers_curate.py): cap centres. Mast foot = cap - (6.4, 16.0) m (measured lean).
_keep = [tuple(p) for p in json.load(open(os.path.join(HERE, 'data', spec['name'], 'towers_curated.json')))]
_LEAN = (6.4, 16.0)
""" + s[b:]
# lattice: interpolate the mast centre from the foot to the cap so the mast leans like the photos
s = s.replace("""    def leg(i, z):
        w = 0.6 + 1.0 * (z - z0) / H          # half-width 0.6 m at the foot, 1.6 m at the head
        sx, sy = ((1, 1), (-1, 1), (-1, -1), (1, -1))[i]
        return (x + sx * w, y + sy * w, z)""", """    fx, fy = x - _LEAN[0], y - _LEAN[1]
    def leg(i, z):
        f = (z - z0) / H; w = 0.6 + 1.0 * f       # half-width 0.6 m at the foot, 1.6 m at the head
        sx, sy = ((1, 1), (-1, 1), (-1, -1), (1, -1))[i]
        return (fx + (x - fx) * f + sx * w, fy + (y - fy) * f + sy * w, z)""")
# base box (white, 5 x 5 x 6 m) at the foot, and the 5-slat solar canopy (12 x 9 m, 5 m up) beside the cap (aerial offsets)
s = s.replace("def _flat(nm, col, rough, metal):", """_BV, _BF = [], []
def _box(cx, cy, z0, hx, hy, h):
    n = len(_BV)
    for zz in (z0, z0 + h):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)): _BV.append((cx + sx * hx, cy + sy * hy, zz))
    _BF.extend([(n + 4, n + 5, n + 6, n + 7)] + [(n + i, n + (i + 1) % 4, n + 4 + (i + 1) % 4, n + 4 + i) for i in range(4)])
_PV, _PF = [], []
for (x, y) in _keep:
    fx, fy = x - _LEAN[0], y - _LEAN[1]; z0 = float(height([fx], [fy])[0])
    _box(fx - 3.2, fy + 0.5, z0, 2.5, 2.5, 6.0)                      # base pylon box beside the mast foot
    cx, cy = x - 6.0, y + 3.0; zc = float(height([cx], [cy])[0]) + 5.0
    for k in range(5):                                                # five slats, 1.4 m wide, 9 m long, 1.9 m pitch
        n = len(_PV); yy = cy - 3.8 + k * 1.9
        for sx, sy in ((-6, -0.7), (6, -0.7), (6, 0.7), (-6, 0.7)): _PV.append((cx + sx, yy + sy, zc + sy * 0.3))
        _PF.append((n, n + 1, n + 2, n + 3))
    for sx in (-5, 5):
        _beam((cx + sx, cy - 3.8, zc - 5.0), (cx + sx, cy - 3.8, zc), 0.12); _beam((cx + sx, cy + 3.8, zc - 5.0), (cx + sx, cy + 3.8, zc), 0.12)
def _flat(nm, col, rough, metal):""")
s = s.replace("print('boulevard towers', len(_keep))", """_o3 = mk_obj('bg_blvd_tower_bases', _BV, _BF, _flat('tower_base', [214, 214, 208], 0.8, 0.0)); set_uv_box(_o3.data, 1.0)
_o4 = mk_obj('bg_blvd_tower_pv', _PV, _PF, _flat('tower_pv', [38, 46, 62], 0.3, 0.2)); set_uv_box(_o4.data, 1.0)
print('boulevard towers', len(_keep))""")
open('accor_towers.py', 'w', newline='').write(s); print('ok', s.count('_LEAN'), s.count('tower_pv'))
