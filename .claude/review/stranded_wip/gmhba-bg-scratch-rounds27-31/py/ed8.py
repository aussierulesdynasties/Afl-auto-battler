import sys
p = sys.argv[1]; s = open(p, newline='').read()
i = s.index('# far suburb tile'); j = s.index("print('ok'")
s = s[:i] + '''# far suburb tile: 1024 px = 500 m; irregular street blocks lined with houses, yards, tree crowns, low-frequency mottle
NS = 1024; m = NS / 500.0; F = Image.new('RGB', (NS, NS), (108, 114, 96)); d = ImageDraw.Draw(F)
RC = [(150, 82, 64), (168, 96, 74), (120, 122, 126), (176, 176, 170), (96, 100, 106), (140, 72, 58), (196, 192, 184), (132, 110, 92)]
xs = np.cumsum(rng.uniform(70, 130, 6)); xs = np.concatenate([[0], xs[xs < 492]]); ys = np.cumsum(rng.uniform(90, 160, 5)); ys = np.concatenate([[0], ys[ys < 486]])
for x_ in xs: d.rectangle([x_ * m - 6, 0, x_ * m + 6, NS], fill=(132, 132, 128))
for y_ in ys: d.rectangle([0, y_ * m - 6, NS, y_ * m + 6], fill=(132, 132, 128))
xe = list(xs) + [500]; ye = list(ys) + [500]
for a0, a1 in zip(xe[:-1], xe[1:]):
    for b0, b1 in zip(ye[:-1], ye[1:]):
        for side in (0, 1):   # two rows of houses per block, fronting the long streets
            yy = b0 + 8 if side == 0 else b1 - 24
            x_ = a0 + 6
            while x_ < a1 - 14:
                w_ = rng.uniform(9, 15); h_ = rng.uniform(12, 17)
                if rng.random() > 0.08: d.rectangle([x_ * m, (yy + rng.uniform(0, 3)) * m, (x_ + w_) * m, (yy + h_) * m], fill=RC[int(rng.integers(0, len(RC)))])
                x_ += w_ + rng.uniform(3, 7)
for _ in range(1300):
    cx, cy, r = rng.uniform(0, 500), rng.uniform(0, 500), rng.uniform(2.5, 6); g = int(rng.integers(0, 3))
    d.ellipse([(cx - r) * m, (cy - r) * m, (cx + r) * m, (cy + r) * m], fill=[(62, 84, 48), (74, 96, 56), (56, 74, 46)][g])
F = F.filter(ImageFilter.GaussianBlur(0.8)); fa = np.asarray(F).astype(float)
lo = rng.normal(0, 1, (8, 8)); lo = np.asarray(Image.fromarray(((lo - lo.min()) / (np.ptp(lo)) * 255).astype(np.uint8)).resize((NS, NS), Image.BICUBIC)).astype(float) / 255
fa = fa * (0.86 + 0.28 * lo[:, :, None]) + rng.normal(0, 4, (NS, NS, 1))
fa = np.clip(fa, 0, 255).astype(np.uint8); Image.fromarray(fa).save(os.path.join(O, 'far_suburb.png'))
open(os.path.join(O, 'far_suburb.mean'), 'w').write('%.4f' % lmean(fa.astype(float)))
''' + s[j:]
open(p, 'w', newline='').write(s); print('ok')
