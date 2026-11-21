s = open('bake_ground.py', encoding='utf-8', newline='').read()
a = "p = os.path.join(D, 'ground_baked.png')"
assert s.count(a) == 1
s = s.replace(a, """# grass: mowing stripes (9 m bands, direction per 160 m block) and wear toward straw by 50 m noise
m_ = 2 * NE / S; R_ = np.random.default_rng(7)
wn = np.asarray(Image.fromarray((R_.random((int(2 * NE / 50) + 2,) * 2) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32) / 255
bd = R_.integers(0, 4, (int(2 * NE / 160) + 2,) * 2); straw = np.array([186, 172, 120], np.float32)
xs = -NE + (np.arange(S) + 0.5) * m_
for r0 in range(0, S, 512):
    rr = np.arange(r0, min(S, r0 + 512)); ys = NE - (rr + 0.5) * m_
    X_, Y_ = np.meshgrid(xs, ys); o = out[rr].astype(np.float32)
    gm = (o[..., 1] > o[..., 0] * 1.08) & (o[..., 1] > o[..., 2] * 1.15)
    ang = bd[((Y_ + NE) // 160).astype(int), ((X_ + NE) // 160).astype(int)] * (np.pi / 4)
    sv = X_ * np.cos(ang) + Y_ * np.sin(ang)
    f = 1 + 0.07 * np.tanh(3 * np.sin(2 * np.pi * sv / 18.0))
    w = 0.22 * np.clip((wn[rr] - 0.55) / 0.45, 0, 1)
    g2 = (o * f[..., None]) * (1 - w[..., None]) + straw * w[..., None]
    out[rr] = np.where(gm[..., None], np.clip(g2, 0, 255), o).astype(np.uint8)
p = os.path.join(D, 'ground_baked.png')""")
open('bake_ground.py', 'w', encoding='utf-8', newline='').write(s); print('ok')
