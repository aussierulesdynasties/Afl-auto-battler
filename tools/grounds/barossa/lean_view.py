"""The model as the 2026 Google aerial sees it, to measure building outlines against the mosaic.

The aerial is not straight down: everything tall leans away from the camera, north-north-east. The four light
towers measure it: each head shows 9.3 m east and 21.3 m north of its base (from the base where the shadow starts),
and the solved drone photo (barossa-park.jpg, camera fitted to the fence, the east crossing and the south goal posts,
0.3 px median on the fence) puts those heads 31-35 m up, mean 32.7. So a point h metres up shows LEAN * h from its
footprint. Roofs and stands traced straight off the mosaic are therefore their tops' positions, several metres north
of where they stand; ground lines (fence, roads, kerbs, slab edges, wall feet, the starts of shadows) are true.

    python3 tools/grounds/barossa/lean_view.py [node ...]    # work/lean_<node>.png and the outline errors

Each node is projected the aerial's way (E + LEAN_E h, N + LEAN_N h), its silhouette filled at 0.2 m, and its outline
is checked against the mosaic: along the outline's normal, the strongest colour edge within 3 m. Reported: median and
90th percentile of that distance, metres."""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

LEAN = (9.3 / 32.7, 21.3 / 32.7)   # metres sideways per metre up, east and north
RES, HALF = 0.2, 150.0


def nodes(names):
    import build
    from dem import Dem
    build.materials()
    dem = Dem(15, 600)
    _, site_h = build.build_site(dem)
    fns = {"towers": lambda mm: build.build_towers(mm, site_h), "clubrooms": build.build_club,
           "terraces": build.build_terraces, "pavilion": build.build_pavilion,
           "temp_stands": lambda mm: build.build_temp_stands(mm, site_h),
           "others": lambda mm: build.build_others(mm, site_h)}
    out = {}
    for n in names:
        m = build.Mesh()
        fns[n](m)
        out[n] = np.concatenate([np.array(p["v"], float) for p in m.parts.values() if p["v"]])
    return out


def silhouette(V):
    """glTF vertices (x east, y up, z south), three a triangle -> the aerial's silhouette mask over the mosaic"""
    import cv2
    E = V[:, 0] + LEAN[0] * V[:, 1]
    N = -V[:, 2] + LEAN[1] * V[:, 1]
    px = np.stack([(E + HALF) / RES, (HALF - N) / RES], 1).reshape(-1, 3, 2)
    mask = np.zeros((int(2 * HALF / RES),) * 2, np.uint8)
    cv2.fillPoly(mask, np.round(px * 4).astype(np.int32), 1, shift=2)
    return mask


def edge_error(a, mask, reach=3.0):
    """distance from each outline pixel to the mosaic's strongest edge along the outline's normal (metres)"""
    import cv2
    lab = cv2.cvtColor(cv2.GaussianBlur(a, (0, 0), 1.0), cv2.COLOR_BGR2LAB).astype(np.float32)
    gx = sum(cv2.Sobel(lab[..., k], cv2.CV_32F, 1, 0) ** 2 for k in range(3))
    gy = sum(cv2.Sobel(lab[..., k], cv2.CV_32F, 0, 1) ** 2 for k in range(3))
    g = np.sqrt(gx + gy)
    m = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 2.0)
    nx, ny = cv2.Sobel(m, cv2.CV_32F, 1, 0), cv2.Sobel(m, cv2.CV_32F, 0, 1)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    d = []
    steps = np.arange(-reach, reach + 0.01, RES)
    for c in cnts:
        for x, y in c[::3, 0]:
            n = np.array((nx[y, x], ny[y, x]))
            if np.linalg.norm(n) < 1e-6:
                continue
            n /= np.linalg.norm(n)
            xs = np.clip(np.round(x + n[0] * steps / RES).astype(int), 0, g.shape[1] - 1)
            ys = np.clip(np.round(y + n[1] * steps / RES).astype(int), 0, g.shape[0] - 1)
            d.append(abs(steps[int(np.argmax(g[ys, xs]))]))
    return np.array(d)


def main():
    import cv2
    names = sys.argv[1:] or ["clubrooms", "pavilion", "terraces", "temp_stands", "towers", "others"]
    a = cv2.imread(os.path.join(HERE, "work", "z20.png"))
    for n, V in nodes(names).items():
        mask = silhouette(V)
        d = edge_error(a, mask)
        print("%-12s outline vs mosaic edges: median %.2f m, 90%% within %.2f m (%d samples)"
              % (n, np.median(d), np.percentile(d, 90), len(d)))
        ys, xs = np.nonzero(mask)
        y0, y1, x0, x1 = max(ys.min() - 60, 0), ys.max() + 60, max(xs.min() - 60, 0), xs.max() + 60
        v = a.copy()
        cnts, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(v, cnts, -1, (0, 0, 255), 1)
        cv2.imwrite(os.path.join(HERE, "work", "lean_%s.png" % n), v[y0:y1, x0:x1])


if __name__ == "__main__":
    main()
