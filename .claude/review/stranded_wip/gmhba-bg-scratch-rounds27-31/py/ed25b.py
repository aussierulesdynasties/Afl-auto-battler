import sys
p = sys.argv[1]; s = open(p, encoding='utf-8', newline='').read()
a = "uk, inv = np.unique(key, return_inverse=True); inv = inv.ravel()\n"
b = a + """farm = farm & (SA[..., 2] <= SA[..., 0] + 2)   # land-coloured pixels only (no sea, swamp or salt-pan blue)
def _bl(x, r):
    k = 2 * r + 1; q = np.pad(x.astype(np.float64)[::8, ::8], r, mode='edge'); c = np.pad(q.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    o = (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]); return np.asarray(Image.fromarray(o.astype(np.float32), 'F').resize((N, N), Image.BILINEAR))
_fw = _bl(farm, 12); REG = np.stack([_bl(SA[..., c] * farm, 12) / np.maximum(_fw, 1e-3) for c in range(3)], -1)   # 1.4 km regional farm colour
"""
s = s.replace(a, b)
a = "    m = np.where(cn > 20, sm / np.maximum(cn, 1), np.nan); m[np.isnan(m)] = np.nanmedian(m)\n    col[..., ch] = m[inv].reshape(N, N) * 1.08 + 6"
assert a in s
b = """    tot = np.bincount(inv, None, len(uk)); fr = (cn / np.maximum(tot, 1))[inv].reshape(N, N)
    m = (sm / np.maximum(cn, 1))[inv].reshape(N, N); t = np.clip((fr - 0.2) / 0.4, 0, 1)
    col[..., ch] = (m * t + REG[..., ch] * (1 - t)) * 1.08 + 6"""
s = s.replace(a, b); open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
