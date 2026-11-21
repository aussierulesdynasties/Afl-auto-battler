p='scene.py'; s=open(p,encoding='utf-8',newline='').read()
old="""        w = b['w']
        box_strip(P, z, w, 1.4, deck_c)"""
new="""        w = b['w']
        if b['w'] <= 6:   # footbridge deck: straight ramp between its two end heights, square piers every 25 m down to the ground
            e0, e1 = float(ends[0]) + 0.3, float(ends[1]) + 0.3; cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))]); tot = max(cum[-1], 1e-6)
            for i in range(len(P) - 1):
                za, zb = e0 + (e1 - e0) * cum[i] / tot, e0 + (e1 - e0) * cum[i + 1] / tot
                d_ = P[i + 1] - P[i]; L = np.hypot(*d_)
                if L < 0.1: continue
                nx, ny = -d_[1] / L * w / 2, d_[0] / L * w / 2; s0 = len(verts)
                for (qx, qy), zz in zip([(P[i][0] + nx, P[i][1] + ny), (P[i + 1][0] + nx, P[i + 1][1] + ny), (P[i + 1][0] - nx, P[i + 1][1] - ny), (P[i][0] - nx, P[i][1] - ny)], (za, zb, zb, za)): verts.append((qx, qy, zz))
                for (qx, qy), zz in zip([(P[i][0] + nx, P[i][1] + ny), (P[i + 1][0] + nx, P[i + 1][1] + ny), (P[i + 1][0] - nx, P[i + 1][1] - ny), (P[i][0] - nx, P[i][1] - ny)], (za, zb, zb, za)): verts.append((qx, qy, zz - 1.0))
                for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)): faces.append(tuple(s0 + k for k in f)); cols.extend([deck_c] * 4)
            for d in np.arange(12.5, tot - 5, 25.0):
                k = int(np.searchsorted(cum, d)) - 1; k = min(max(k, 0), len(P) - 2); t = (d - cum[k]) / max(cum[k + 1] - cum[k], 1e-6)
                px, py = P[k] + (P[k + 1] - P[k]) * t; zt = e0 + (e1 - e0) * d / tot - 1.0; zg = float(height(np.array([px]), np.array([py]))[0])
                if zt - zg < 1.0: continue
                s0 = len(verts)
                for zz in (zt, zg - 0.5):
                    for ox, oy in ((-0.4, -0.4), (0.4, -0.4), (0.4, 0.4), (-0.4, 0.4)): verts.append((px + ox, py + oy, zz))
                for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)): faces.append(tuple(s0 + k2 for k2 in f)); cols.extend([deck_c] * 4)
            for sd in (-1, 1):   # railings 1.1 m on each edge, following the ramp
                for i in range(len(P) - 1):
                    d_ = P[i + 1] - P[i]; L = np.hypot(*d_)
                    if L < 0.1: continue
                    o = sd * np.array([-d_[1], d_[0]]) / L * (w / 2 - 0.1); za, zb = e0 + (e1 - e0) * cum[i] / tot, e0 + (e1 - e0) * cum[i + 1] / tot; s0 = len(verts)
                    for (qx, qy), zz in zip([P[i] + o, P[i + 1] + o, P[i + 1] + o, P[i] + o], (za, zb, zb + 1.1, za + 1.1)): verts.append((qx, qy, zz))
                    faces.append((s0, s0 + 1, s0 + 2, s0 + 3)); cols.extend([rail_c] * 4)
            continue
        box_strip(P, z, w, 1.4, deck_c)"""
assert s.count(old)==1; s=s.replace(old,new); open(p,'w',encoding='utf-8',newline='').write(s); print('ok')
