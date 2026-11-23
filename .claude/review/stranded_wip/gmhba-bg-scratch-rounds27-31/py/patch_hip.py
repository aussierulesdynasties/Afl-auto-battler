import io
f = 'scene.py'; s = io.open(f, encoding='utf-8', newline='').read()
def sub(a, b):
    global s; assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
sub("BL = json.load(open(os.path.join(D, 'buildings.json')))",
"""BL = json.load(open(os.path.join(D, 'buildings.json')))
def hip_rect(P):   # minimum-area rectangle: centre, long-axis unit u, short-axis unit v, length L, width W
    best = None
    for i in range(len(P)):
        e = P[(i + 1) % len(P)] - P[i]; n_ = float(np.hypot(*e))
        if n_ < 1e-6: continue
        u = e / n_; v = np.array([-u[1], u[0]]); pu, pv = P @ u, P @ v
        ar = (pu.max() - pu.min()) * (pv.max() - pv.min())
        if best is None or ar < best[0]: best = (ar, u, v, pu.min(), pu.max(), pv.min(), pv.max())
    _, u, v, a0, a1, b0, b1 = best
    if a1 - a0 < b1 - b0: u, v, a0, a1, b0, b1 = v, -u, b0, b1, -a1, -a0
    return u * (a0 + a1) / 2 + v * (b0 + b1) / 2, u, v, a1 - a0, b1 - b0""")
sub("        pitched = cls == 'house' and len(P) <= 8\n        rh = min(2.6, math.sqrt(abs(b.get('a', 150))) / 5) if pitched else 0",
"        pitched = cls == 'house'\n        if pitched: hc, hu, hv, hL, hW = hip_rect(P); rh = min(3.4, (hW / 2 + 0.45) * math.tan(math.radians(25)))\n        else: rh = 0")
i = s.index("        if pitched:\n", s.index("for x, y in P: rv.append"))
j = s.index("        else:\n", i)
s = s[:i] + """        if pitched:   # hip roof on the footprint's rectangle: 0.45 m eaves, ridge along the long side, 25 degree pitch
            del rv[r0:]; del ruv[r0:]
            eL, eW = hL / 2 + 0.45, hW / 2 + 0.45; rr = max(0.0, eL - eW)
            E4 = [hc - hu * eL - hv * eW, hc + hu * eL - hv * eW, hc + hu * eL + hv * eW, hc - hu * eL + hv * eW]
            R2 = [hc - hu * rr, hc + hu * rr]
            for q in E4: rv.append((q[0], q[1], top)); ruv.append(ruv_(q[0], q[1]))
            for q in R2: rv.append((q[0], q[1], top + rh)); ruv.append(ruv_(q[0], q[1]))
            for fc in ((0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4)):
                rf.append(tuple(r0 + t_ for t_ in fc)); rcl += [rc] * len(fc)
""" + s[j:]
io.open(f, 'w', encoding='utf-8', newline='').write(s); print('ok')
