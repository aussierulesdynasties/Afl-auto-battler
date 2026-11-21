# Coastline (exec'd by scene.py after the far terrain colours, when spec['coast_v2']). The shore follows the real OSM
# coastline (data/<name>/coast.json, natural=coastline: land on the left), not the 250 m terrain contour: far cells within
# 400 m of it are re-cut into 10 m cells, water-side points drop under the sea plane, land-side points sit just above it,
# and a 9 m band along the land edge gets the sea-wall/beach colour. Shares VF, FF, vc, hz, st, WV, ZSEA, FA, FS, m, lin, spec, np.
_lat0, _lon0 = spec['lat'], spec['lon']; _KX = 111320 * math.cos(math.radians(_lat0)); _KY = 110540
_cj = json.load(open(os.path.join(HERE, 'data', name, 'coast.json')))['elements']
SEG = []
for e in _cj:
    t = e.get('tags', {})
    if t.get('natural') != 'coastline': continue
    P = np.array([((g['lon'] - _lon0) * _KX, (g['lat'] - _lat0) * _KY) for g in e['geometry']])
    SEG += [(P[i], P[i + 1]) for i in range(len(P) - 1)]
SA = np.array([s[0] for s in SEG]); SB = np.array([s[1] for s in SEG]); SD = SB - SA; SL2 = np.maximum((SD ** 2).sum(1), 1e-9)
def coast_sd(Q, sub=None):   # signed distance to the coastline: + land (left of the way), - water
    A_, D_, L2_ = (SA, SD, SL2) if sub is None else (SA[sub], SD[sub], SL2[sub])
    out = np.empty(len(Q))
    for i0 in range(0, len(Q), 800):
        q = Q[i0:i0 + 800]; w = q[:, None, :] - A_[None]
        t = np.clip((w * D_[None]).sum(2) / L2_[None], 0, 1); c = A_[None] + t[..., None] * D_[None]
        d2 = ((q[:, None, :] - c) ** 2).sum(2); k = d2.argmin(1); r = np.arange(len(q))
        cr = D_[k, 0] * w[r, k, 1] - D_[k, 1] * w[r, k, 0]
        out[i0:i0 + 800] = np.sqrt(d2[r, k]) * np.where(cr >= 0, 1, -1)
    return out
SMID = (SA + SB) / 2; SHL = np.sqrt(SL2) / 2
CN = 25
_cc = (VF[FF[:, 0], :2] + VF[FF[:, 2], :2]) / 2
_near = (np.abs(coast_sd(_cc)) < 400) & (np.hypot(_cc[:, 0], _cc[:, 1]) < spec.get('coast_refine_r', 9000))
_sel = np.where(_near)[0]; _key = {tuple(np.round(_cc[i] / FS).astype(int)): i for i in _sel}
print('coast cells refined', len(_sel), 'segments', len(SEG))
_nv, _nf, _nc, _nh, _ns, _nw, _ne = [], [], [], [], [], [], []
_base = len(VF); _keep = np.ones(len(FF), bool)
for i in _sel:
    a0, a1, a2, a3 = FF[i]; P0, P1, P2, P3 = VF[a0], VF[a1], VF[a2], VF[a3]   # quad corners: (i,j) (i+1,j) (i+1,j+1) (i,j+1)
    C0, C1, C2, C3 = vc[a0], vc[a1], vc[a2], vc[a3]; H0, H1, H2, H3 = hz[a0], hz[a1], hz[a2], hz[a3]
    kc = np.round(_cc[i] / FS).astype(int)
    nb = {(-1, 0): tuple(kc + (-1, 0)) in _key, (1, 0): tuple(kc + (1, 0)) in _key, (0, -1): tuple(kc + (0, -1)) in _key, (0, 1): tuple(kc + (0, 1)) in _key}
    u = np.linspace(0, 1, CN + 1); U, V = np.meshgrid(u, u); U = U.ravel(); V = V.ravel()
    w0 = (1 - U) * (1 - V); w1 = U * (1 - V); w2 = U * V; w3 = (1 - U) * V
    Pq = w0[:, None] * P0 + w1[:, None] * P1 + w2[:, None] * P2 + w3[:, None] * P3
    Cq = w0[:, None] * C0 + w1[:, None] * C1 + w2[:, None] * C2 + w3[:, None] * C3
    Hq = w0[:, None] * H0 + w1[:, None] * H1 + w2[:, None] * H2 + w3[:, None] * H3
    border = ((U == 0) & ~nb[(-1, 0)]) | ((U == 1) & ~nb[(1, 0)]) | ((V == 0) & ~nb[(0, -1)]) | ((V == 1) & ~nb[(0, 1)])
    _sub_ = np.where(np.hypot(*(SMID - _cc[i]).T) - SHL < 1200)[0]; sd = coast_sd(Pq[:, :2], _sub_); free = ~border
    wat = (sd < 0) & free; lnd = (sd >= 0) & free
    Pq[wat, 2] = np.minimum(Pq[wat, 2], ZSEA - 3.0)
    Pq[lnd, 2] = np.maximum(Pq[lnd, 2], ZSEA + 1.5 + np.minimum(sd[lnd], 200) * 0.01)
    edge = lnd & (sd < 9.0)
    Cq[edge] = Cq[edge] * 0 + lin((176, 168, 146))[:3] * (1 - Hq[edge]) + lin(PAL['haze'])[:3] * Hq[edge]   # bluestone wall / sand edge
    o = _base + len(_nv); _nv += Pq.tolist(); _nc += Cq.tolist(); _nh += Hq.tolist(); _ns += [float(st.ravel()[[a0, a1, a2, a3]].max())] * len(Pq); _nw += list(sd < 0); _ne += list(edge)
    for jj in range(CN):
        for ii in range(CN):
            q = o + jj * (CN + 1) + ii; _nf.append((q, q + 1, q + CN + 2, q + CN + 1))
    _keep[i] = False
if _nv:
    VF = np.concatenate([VF, np.array(_nv)]); vc = np.concatenate([vc, np.array(_nc, vc.dtype)]); hz = np.concatenate([hz, np.array(_nh).reshape(-1, 1)])
    st = np.concatenate([st.reshape(-1, 1), np.array(_ns).reshape(-1, 1)]); WV = np.concatenate([WV.ravel(), np.array(_nw, bool)])
    FF = np.concatenate([FF[_keep], np.array(_nf)])
    _ev = np.concatenate([np.zeros(_base, bool), np.array(_ne, bool)]); SHOREF = _ev[FF].any(1)
COAST_SD = coast_sd
