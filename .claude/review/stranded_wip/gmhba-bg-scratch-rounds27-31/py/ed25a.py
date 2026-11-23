import sys
p = sys.argv[1]; s = open(p, encoding='utf-8', newline='').read()
a = "col = np.array([u for u, _ in USES], np.float32)[np.clip(ui, 0, len(USES) - 1)]\n"
assert a in s
b = a + """# measured colour: each paddock takes the median colour of the reference aerial (sat_far.png, 30 m/px) over its own
# area, so the patchwork follows the real dry-brown / olive / green distribution; land use from landuse.npy
SA = np.asarray(Image.open(os.path.join(H, 'data', 'gmhba', 'sat_far.png')).resize((N, N), Image.BILINEAR)).astype(np.float32)
LU = np.asarray(Image.fromarray(np.load(os.path.join(H, 'data', 'gmhba', 'landuse.npy'))).resize((N, N), Image.NEAREST))
key = np.round(pid * 1e6).astype(np.int64) * 7 + (bu * 1009 + bv).astype(np.int64); farm = LU == 0
uk, inv = np.unique(key, return_inverse=True); inv = inv.ravel()
for ch in range(3):
    v = SA[..., ch].ravel(); w = farm.ravel().astype(np.float64)
    sm = np.bincount(inv, v * w, len(uk)); cn = np.bincount(inv, w, len(uk))
    m = np.where(cn > 20, sm / np.maximum(cn, 1), np.nan); m[np.isnan(m)] = np.nanmedian(m)
    col[..., ch] = m[inv].reshape(N, N) * 1.08 + 6   # scene exposure lifts the aerial's dark JPEG midtones slightly
"""
s = s.replace(a, b)
a2 = "col = col * 0.7 + col.mean(2, keepdims=True) * 0.3   # summer haze takes the edge off the colour\n"
assert a2 in s
b2 = """urb = LU == 1; fo = LU == 2   # towns: grey roof/street speckle on a 100 m block grid; forest: dark canopy clumps
blk = ((np.abs((X % 100) - 50) > 44) | (np.abs((Y % 100) - 50) > 44))
uc = np.array((126, 122, 116), np.float32) * (0.85 + 0.3 * R.random((N, N)))[..., None]; uc[blk] = (100, 100, 98)
col[urb] = uc[urb] * 0.8 + np.array((92, 104, 76), np.float32) * 0.2   # gardens and street trees
fc = np.array((52, 66, 44), np.float32) * (0.75 + 0.5 * np.clip(1 + smooth(120, 12, 0.5), 0, 2) / 2)[..., None]
col[fo] = fc[fo]
""" + a2
s = s.replace(a2, b2)
open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
