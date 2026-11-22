# Individual sails from the aerial: dark fabric pixels inside each sail field, eroded apart, one oriented rectangle each.
import json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
CP = np.array(json.load(open('data/riverway/prep/carports_cls.json')), float)
im = np.asarray(Image.open('data/riverway/sat.png').convert('RGB')).astype(float)
gray = im.mean(2)
out = []
for g in (1, 2, 3):
    S = CP[CP[:, 4] == g][:, :2]; x0, y0 = S.min(0) - 6; x1, y1 = S.max(0) + 6
    r0, r1, c0, c1 = int((1600 - y1) * 2), int((1600 - y0) * 2), int((x0 + 1600) * 2), int((x1 + 1600) * 2)
    G = gray[r0:r1, c0:c1]
    thr = np.percentile(G[G < 110], 55)
    M = (G < thr)
    M = nd.binary_opening(M, iterations=2)
    E = nd.binary_erosion(M, iterations=3)
    L, n = nd.label(E)
    vis = Image.fromarray(im[r0:r1, c0:c1].astype(np.uint8)).resize(((c1 - c0) * 2, (r1 - r0) * 2)); d = ImageDraw.Draw(vis)
    k = 0
    for i in range(1, n + 1):
        rr, cc = np.nonzero(L == i)
        a = len(rr) * 0.25
        if a < 25 or a > 260: continue
        P = np.stack([cc, rr], 1).astype(float); c = P.mean(0); w, v = np.linalg.eigh(np.cov((P - c).T))
        ax = v[:, 1]; bx = v[:, 0]; u = (P - c) @ ax; t = (P - c) @ bx
        hu, ht = (u.max() - u.min()) / 2 + 3, (t.max() - t.min()) / 2 + 3          # add back the erosion
        cn = [c + ax * su * hu + bx * st * ht for su, st in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        d.polygon([(p[0] * 2, p[1] * 2) for p in cn], outline=(255, 0, 0)); k += 1
        wx = [((p[0] + c0) / 2 - 1600, 1600 - (p[1] + r0) / 2) for p in cn]
        out.append({'g': g, 'corners': wx, 'size': [round(hu), round(ht)]})
    vis.save(f'out/riverway/chk/saildet_{g}.png'); print('field', g, 'sails', k)
json.dump(out, open('data/riverway/prep/sails.json', 'w'))
