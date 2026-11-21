"""Lead's 4th list: water ripple/glint/shore, grass tonal variation, darker far land without repeat."""
import shutil
def patch(fn, pairs):
    shutil.copy(fn, fn.replace('.py', '_pre7.py')); s = open(fn, encoding='utf-8', newline='').read()
    for a, b in pairs:
        assert s.count(a) == 1, (fn, a[:60]); s = s.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='').write(s)
if 0: patch('bake_ground.py', [
("xs = -NE + (np.arange(S) + 0.5) * m_\n",
"""xs = -NE + (np.arange(S) + 0.5) * m_
def _nz(cell, seed, ax=None):   # value noise at a cell size in metres (ax: (rows, cols) cell sizes for streaks)
    r = np.random.default_rng(seed); cy, cx = (cell, cell) if ax is None else ax
    return np.asarray(Image.fromarray((r.random((int(2 * NE / cy) + 2, int(2 * NE / cx) + 2)) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32) / 255
_o0 = out.astype(np.int16); GM = ((_o0[..., 1] > _o0[..., 0] * 1.08) & (_o0[..., 1] > _o0[..., 2] * 1.15)); del _o0
GB = np.asarray(Image.fromarray((GM * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5 / m_)), np.float32) / 255
N80, N300, NDMP, NTF = _nz(80, 21), _nz(300, 22), _nz(22, 23), _nz(1.6, 24)
"""),
("    out[rr] = np.where(gm[..., None], np.clip(g2, 0, 255), o).astype(np.uint8)\n",
"""    tone = 1 + 0.16 * (N80[rr] - 0.5) + 0.22 * (N300[rr] - 0.5) + 0.12 * (NTF[rr] - 0.5)   # broad and tuft variation
    damp = np.clip((NDMP[rr] - 0.66) / 0.14, 0, 1) * (1 - PM[rr])                           # darker damp blotches
    edg = 1 - 0.22 * np.clip((0.97 - GB[rr]) / 0.45, 0, 1)                                    # darker along paths, water, kerbs
    g2 = g2 * (tone * edg)[..., None]; g2 = g2 * (1 - 0.3 * damp[..., None]) + np.array([46, 70, 48], np.float32) * 0.3 * damp[..., None]
    out[rr] = np.where(gm[..., None], np.clip(g2, 0, 255), o).astype(np.uint8)
"""),
("shallow = np.array([96, 120, 118], np.float32)",
"""RIP = _nz(0, 31, (3.0, 26.0)); RIP2 = _nz(0, 32, (7.0, 60.0)); GL = _nz(0, 33, (1.2, 7.0)); GLB = _nz(140, 34)
shallow = np.array([96, 120, 118], np.float32)"""),
("    w = shallow * (1 - t) + chan * t; w = w * (0.92 + 0.16 * tn[rr][..., None])\n",
"""    w = shallow * (1 - t) + chan * t; w = w * (0.92 + 0.16 * tn[rr][..., None])
    w = w * (1 + 0.20 * (RIP[rr] - 0.5) + 0.14 * (RIP2[rr] - 0.5))[..., None]                 # wind ripple streaks
    w = w * (1 - 0.22 * np.clip((0.68 - deep[rr]) / 0.18, 0, 1))[..., None]                    # darker band along the shore
    gl = np.clip((GL[rr] - 0.80) / 0.10, 0, 1) * np.clip((GLB[rr] - 0.35) / 0.3, 0, 1) * t[..., 0]   # sun glint flecks in patches
    w = w * (1 - 0.8 * gl[..., None]) + np.array([214, 224, 226], np.float32) * 0.8 * gl[..., None]
"""),
])
patch('mk_far2.py', [
("np.array([t * (1 + hue), t, t * (1 - hue)]) * 225", "np.array([t * (1 + hue) * 0.86, t, t * (1 - hue) * 0.72]) * 150"),
("rect_wrap(x0, y0, x1, y0 + 4, (118, 128, 104))", "rect_wrap(x0, y0, x1, y0 + 4, (62, 80, 52))"),
("rect_wrap(x0, y0, x0 + 4, y1, (118, 128, 104))", "rect_wrap(x0, y0, x0 + 4, y1, (62, 80, 52))"),
("a[m] = [214, 214, 200]", "a[m] = a[m] * 0.6 + np.array([150, 150, 138]) * 0.4"),
("a = np.asarray(im, np.float32)[n:2 * n, n:2 * n].copy()", "a = np.asarray(im, np.float32)[n:2 * n, n:2 * n].copy(); a = a.mean(-1, keepdims=True) * 0.35 + a * 0.65 + 0"),
])
patch('scene.py', [
("vc = np.clip(vc * 1.3, 0, 1)   # the farmland tile averages 0.76: lift so the mean tone is kept",
"_bn = 1 + 0.18 * np.sin(VF[:, 0] / 1300 + 1.3) * np.sin(VF[:, 1] / 1700 + 0.4) + 0.12 * np.sin((VF[:, 0] + VF[:, 1]) / 2300); vc = np.clip(vc * 1.75 * _bn[:, None], 0, 1)   # km-scale tone swells break the tile repeat; tile now darker"),
])
print('ok')
