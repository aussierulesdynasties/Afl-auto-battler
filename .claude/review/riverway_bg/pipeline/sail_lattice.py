# Fit a rotated lattice of square sails to aerial darkness per field: sail size s, pitch p, angle, offsets.
# Score = darkness inside sails - darkness in the gaps, over the field mask. Keeps lattice cells whose sail area is mostly dark.
import json, numpy as np
from PIL import Image, ImageDraw
CP = np.array(json.load(open('data/riverway/prep/carports_cls.json')), float)
im = np.asarray(Image.open('data/riverway/sat.png').convert('RGB')).astype(float); gray = im.mean(2)
out = []
for g in (1, 2, 3):
    S = CP[CP[:, 4] == g][:, :2]; x0, y0 = S.min(0) - 8; x1, y1 = S.max(0) + 8
    xs = np.arange(x0, x1, 0.5) + 0.25; ys = np.arange(y0, y1, 0.5) + 0.25
    X, Y = np.meshgrid(xs, ys); D = 255 - gray[(1600 - Y).astype(int) * 2 // 1, ((X + 1600) * 2).astype(int)]
    occ = set(map(tuple, np.floor(S).astype(int))); M = np.array([(int(np.floor(x)), int(np.floor(y))) in occ for x, y in zip(X.ravel(), Y.ravel())]).reshape(X.shape)
    Dn = (D - D[M].mean()) / D[M].std(); c = S.mean(0)
    best = None
    for s in (9.0, 10.0, 11.0, 12.0):
        for p in (s + 1, s + 2, s + 3, s + 4):
            for th in np.radians(np.arange(0, 90, 2.0)):
                a = np.array([np.cos(th), np.sin(th)]); b = np.array([-a[1], a[0]])
                U = (X - c[0]) * a[0] + (Y - c[1]) * a[1]; V = (X - c[0]) * b[0] + (Y - c[1]) * b[1]
                for ou in np.arange(0, p, 1.0):
                    for ov in np.arange(0, p, 1.0):
                        fu = np.mod(U - ou, p); fv = np.mod(V - ov, p)
                        ins = (fu < s) & (fv < s)
                        sc = Dn[M & ins].mean() - Dn[M & ~ins].mean()
                        if best is None or sc > best[0]: best = (sc, s, p, th, ou, ov)
    sc, s, p, th, ou, ov = best
    a = np.array([np.cos(th), np.sin(th)]); b = np.array([-a[1], a[0]])
    U = (X - c[0]) * a[0] + (Y - c[1]) * a[1]; V = (X - c[0]) * b[0] + (Y - c[1]) * b[1]
    I = np.floor((U - ou) / p).astype(int); J = np.floor((V - ov) / p).astype(int)
    ins = (np.mod(U - ou, p) < s) & (np.mod(V - ov, p) < s)
    vis = Image.fromarray(im[int((1600 - y1) * 2):int((1600 - y0) * 2), int((x0 + 1600) * 2):int((x1 + 1600) * 2)].astype(np.uint8))
    vis = vis.resize((vis.width * 2, vis.height * 2)); d = ImageDraw.Draw(vis); k = 0
    for i, j in set(zip(I[ins & M], J[ins & M])):
        sel = ins & (I == i) & (J == j)
        if (sel & M).sum() < 0.45 * sel.sum() or sel.sum() < 0.6 * (s * s * 4) or Dn[sel].mean() < -0.3: continue
        cu, cv = i * p + ou + s / 2, j * p + ov + s / 2
        cn = [c + a * (cu + su * s / 2) + b * (cv + sv * s / 2) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        out.append({'g': g, 'corners': [list(map(float, q)) for q in cn]}); k += 1
        d.polygon([((q[0] - x0) * 4, (y1 - q[1]) * 4) for q in cn], outline=(255, 0, 0))
    vis.save(f'out/riverway/chk/saillat_{g}.png')
    print('field', g, 'sails', k, 'size', s, 'pitch', p, 'angle', round(np.degrees(th)), 'score', round(sc, 2))
json.dump(out, open('data/riverway/prep/sails.json', 'w'))
