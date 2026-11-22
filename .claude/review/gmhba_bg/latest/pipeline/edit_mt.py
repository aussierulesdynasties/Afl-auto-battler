p='prep.py'; s=open(p,encoding='utf-8',newline='').read()
a="print('rails', len(RL))"
b="""# roads: asphalt ribbons with lane lines in scene.py (texture pass, director OK 2026-11-20 "Build all three")
RD = []
for el in js:
    t = el.get('tags', {}); hw = t.get('highway')
    if el['type'] != 'way' or hw not in ('motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'service'): continue
    if (t.get('bridge') and t.get('bridge') != 'no') or (t.get('tunnel', 'no') != 'no') or t.get('covered') == 'yes': continue
    pts = ring(el); run = []
    for x, y in pts + [(1e9, 1e9)]:
        if abs(x) < NEAR and abs(y) < NEAR: run.append([round(x, 2), round(y, 2)]); continue
        if len(run) > 1: RD.append(dict(hw=hw, p=run, oneway=t.get('oneway') == 'yes'))
        run = []
json.dump(RD, open(os.path.join(OUT, 'roads.json'), 'w')); print('roads', len(RD))
"""
assert a in s; s=s.replace(a,b+a,1); open(p,'w',encoding='utf-8',newline='').write(s)

p='scene.py'; s=open(p,encoding='utf-8',newline='').read()
# roofs: big light non-house sheds get corrugated iron
a="    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []]}"
assert a in s; s=s.replace(a,"    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []], 'corr': [[], [], [], []]}",1)
a="        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)\n        def ruv_(x, y): return ((x * ct + y * st) / 3.04, (-x * st + y * ct) / 3.04)"
b="""        RT = 3.04
        if kind == 'metal' and cls != 'house' and b['a'] >= 400 and float(np.mean(np.asarray(PAL['roofs_flat'][b['roof'] % len(PAL['roofs_flat'])]))) >= 150: kind, RT = 'corr', 7.2   # big white sheds: corrugated iron (256 px = 3.6 m)
        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)
        def ruv_(x, y): return ((x * ct + y * st) / RT, (-x * st + y * ct) / RT)"""
assert a in s; s=s.replace(a,b,1)
a="os.path.join(HERE, 'tex', 'roof_%s.png' % kind)"
assert a in s; s=s.replace(a,"os.path.join(HERE, 'tex', 'mt/roof_corrugated.png' if kind == 'corr' else 'roof_%s.png' % kind)",1)
# far towers
a="build_class('tower', 'tower.png', 3.0, 3.6)"
b="""for b in BL:   # towers over 1 km out: distant city facade (texture pass)
    if b['c'] == 'tower' and float(np.hypot(*np.array(b['p'], float).mean(0))) > 1000: b['c'] = 'tower_far'
PAL['walls_tower_far'] = PAL['walls_tower']
build_class('tower', 'tower.png', 3.0, 3.6)
build_class('tower_far', 'mt/city_far.png', 12.0, 7.2)"""
assert a in s; s=s.replace(a,b,1)
# roads
a="# ---------- buildings ----------"
b="""# ---------- roads: asphalt ribbons draped on the terrain, lane lines on main roads (texture pass) ----------
RDP = os.path.join(D, 'roads.json')
if os.path.exists(RDP):
    RW = {'motorway': 22, 'trunk': 18, 'primary': 16, 'secondary': 13, 'tertiary': 11, 'residential': 8, 'unclassified': 8, 'service': 5}
    RK = {'service': 0, 'residential': 1, 'unclassified': 1, 'tertiary': 2, 'secondary': 3, 'primary': 4, 'trunk': 5, 'motorway': 6}
    _kf = os.path.join(D, 'footprint.json'); KFr = np.array(json.load(open(_kf))) if os.path.exists(_kf) else None
    av, af, ac, au, lv, lf = [], [], [], [], [], []
    acol = lin(tuple(PAL['road']))
    def ribbon(Q, off, w, z, V_, F_, U_=None, dash=None):
        n = len(Q); D_ = np.gradient(Q, axis=0); D_ /= np.maximum(np.hypot(D_[:, 0], D_[:, 1]), 1e-6)[:, None]
        N_ = np.stack([-D_[:, 1], D_[:, 0]], 1); C = Q + N_ * off; A = C + N_ * w / 2; B = C - N_ * w / 2
        s_ = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
        for i in range(n - 1):
            if dash and (s_[i] % (dash[0] + dash[1])) >= dash[0]: continue
            k = len(V_); V_ += [(A[i, 0], A[i, 1], z[i]), (B[i, 0], B[i, 1], z[i]), (B[i + 1, 0], B[i + 1, 1], z[i + 1]), (A[i + 1, 0], A[i + 1, 1], z[i + 1])]; F_.append((k, k + 1, k + 2, k + 3))
            if U_ is not None: U_ += [(-w / 2 / 7.2, s_[i] / 7.2), (w / 2 / 7.2, s_[i] / 7.2), (w / 2 / 7.2, s_[i + 1] / 7.2), (-w / 2 / 7.2, s_[i + 1] / 7.2)]
    for r in json.load(open(RDP)):
        P = np.array(r['p'], float); Q = [P[0]]
        for p2 in P[1:]:
            k = max(1, int(math.ceil(np.hypot(*(p2 - Q[-1])) / 3.0)))
            for j in range(1, k + 1): Q.append(Q[-1] + (p2 - Q[-1]) * (1.0 / (k - j + 1)))
        Q = np.array(Q); ok = np.ones(len(Q), bool)
        if KFr is not None: ok = np.hypot(Q[:, 0], Q[:, 1]) > KFr[((np.degrees(np.arctan2(Q[:, 1], Q[:, 0])) % 360) // 2).astype(int)] + 1.0
        w = RW[r['hw']]; main = RK[r['hw']] >= 3
        for rr in np.split(np.arange(len(Q)), np.where(np.diff(ok.astype(int)) != 0)[0] + 1):
            if not ok[rr[0]] or len(rr) < 2: continue
            q = Q[rr]; D_ = np.gradient(q, axis=0); D_ /= np.maximum(np.hypot(D_[:, 0], D_[:, 1]), 1e-6)[:, None]; N_ = np.stack([-D_[:, 1], D_[:, 0]], 1)
            zz = np.max([height(q[:, 0] + N_[:, 0] * o, q[:, 1] + N_[:, 1] * o) for o in (-w / 2, 0, w / 2)], 0) + 0.10 + 0.01 * RK[r['hw']]
            n0 = len(af); ribbon(q, 0, w, zz, av, af, au); ac += [acol] * 4 * (len(af) - n0)
            if main:   # white lines: broken centre line (3 m line, 9 m gap) unless one-way; solid edge lines 0.6 m in
                if not r['oneway']: ribbon(q, 0, 0.12, zz + 0.03, lv, lf, dash=(3.0, 9.0))
                for sd in (-1, 1): ribbon(q, sd * (w / 2 - 0.6), 0.12, zz + 0.03, lv, lf)
    if af:
        ro = mk_obj('bg_roads', av, af, mat_facade('road_asphalt', os.path.join(HERE, 'tex', 'mt', 'road_asphalt.png')))
        set_corner_col(ro.data, np.concatenate([np.array(ac), np.ones((len(ac), 1))], 1)); set_uv(ro.data, au)
    if lf:
        lm = bpy.data.materials.new('road_line'); lm.use_nodes = True; lm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.82, 0.82, 0.8, 1)
        mk_obj('bg_road_lines', lv, lf, lm)
    print('roads', len(af), 'quads,', len(lf), 'line quads')

""" + a
assert a in s; s=s.replace(a,b,1)
open(p,'w',encoding='utf-8',newline='').write(s); print('ok')
