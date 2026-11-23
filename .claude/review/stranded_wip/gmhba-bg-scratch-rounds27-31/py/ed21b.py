import sys
p = sys.argv[1]; s = open(p, encoding='utf-8', newline='').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("""def coast_sd(Q):   # signed distance to the coastline: + land (left of the way), - water
    out = np.empty(len(Q))
    for i0 in range(0, len(Q), 4000):
        q = Q[i0:i0 + 4000]; w = q[:, None, :] - SA[None]
        t = np.clip((w * SD[None]).sum(2) / SL2[None], 0, 1); c = SA[None] + t[..., None] * SD[None]
        d2 = ((q[:, None, :] - c) ** 2).sum(2); k = d2.argmin(1); r = np.arange(len(q))
        cr = SD[k, 0] * w[r, k, 1] - SD[k, 1] * w[r, k, 0]
        out[i0:i0 + 4000] = np.sqrt(d2[r, k]) * np.where(cr >= 0, 1, -1)
    return out""", """def coast_sd(Q, sub=None):   # signed distance to the coastline: + land (left of the way), - water
    A_, D_, L2_ = (SA, SD, SL2) if sub is None else (SA[sub], SD[sub], SL2[sub])
    out = np.empty(len(Q))
    for i0 in range(0, len(Q), 800):
        q = Q[i0:i0 + 800]; w = q[:, None, :] - A_[None]
        t = np.clip((w * D_[None]).sum(2) / L2_[None], 0, 1); c = A_[None] + t[..., None] * D_[None]
        d2 = ((q[:, None, :] - c) ** 2).sum(2); k = d2.argmin(1); r = np.arange(len(q))
        cr = D_[k, 0] * w[r, k, 1] - D_[k, 1] * w[r, k, 0]
        out[i0:i0 + 800] = np.sqrt(d2[r, k]) * np.where(cr >= 0, 1, -1)
    return out
SMID = (SA + SB) / 2; SHL = np.sqrt(SL2) / 2""")
rep("_near = np.abs(coast_sd(_cc)) < 400", "_near = (np.abs(coast_sd(_cc)) < 400) & (np.hypot(_cc[:, 0], _cc[:, 1]) < spec.get('coast_refine_r', 9000))")
rep("sd = coast_sd(Pq[:, :2]); free = ~border", "_sub_ = np.where(np.hypot(*(SMID - _cc[i]).T) - SHL < 1200)[0]; sd = coast_sd(Pq[:, :2], _sub_); free = ~border")
open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
