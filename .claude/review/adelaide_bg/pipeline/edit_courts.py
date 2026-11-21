p='prep.py'; s=open(p,newline='').read()
old="""    print('court slabs', len(set(find(i) for i in range(len(CT)))), 'courts', len(CT))"""
new="""    # geometry for scene.py: slab hull per group and each court's oriented box (lines are drawn as real geometry there)
    def _obox(pts):
        Q = np.array(pts, float); best = None
        for i in range(len(Q)):
            d = Q[(i + 1) % len(Q)] - Q[i]
            if np.hypot(*d) < 0.5: continue
            u = d / np.hypot(*d); w = np.array([-u[1], u[0]]); a = Q @ u; b = Q @ w
            area = (a.max() - a.min()) * (b.max() - b.min())
            if best is None or area < best[0]:
                c = u * (a.max() + a.min()) / 2 + w * (b.max() + b.min()) / 2; L_, W_ = a.max() - a.min(), b.max() - b.min()
                best = (area, c, u if L_ >= W_ else w, max(L_, W_), min(L_, W_))
        return [round(float(best[1][0]), 2), round(float(best[1][1]), 2), round(float(math.atan2(best[2][1], best[2][0])), 4), round(float(best[3]), 2), round(float(best[4]), 2)]
    json.dump({'slabs': [[mem_[0][1], _hull([p for m in mem_ for p in m[0]])] for mem_ in ([CT[i] for i in range(len(CT)) if find(i) == r] for r in set(find(i) for i in range(len(CT))))],
               'courts': [[col] + _obox(pts) for pts, col in CT], 'pal': {k: PAL[k] for k in set(c for _, c in CT)}},
              open(os.path.join(OUT, 'courts.json'), 'w'))
    print('court slabs', len(set(find(i) for i in range(len(CT)))), 'courts', len(CT))"""
assert old in s; s=s.replace(old,new); open(p,'w',newline='').write(s); print('ok')
