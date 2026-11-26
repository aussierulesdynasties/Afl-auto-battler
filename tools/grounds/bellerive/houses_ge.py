"""Each Bellerive building's roof, read off Google Earth's straight-down shots (ge_trees.py plans them: 24 shots
from 800 m, 0.5 m a pixel). Only measurements are kept, never imagery (docs/MCG_STANDARD.md: sampled colours are fine).

  python3 houses_ge.py <workdir>     # after surrounds.py has written buildings.bin; writes houses_ge.json here

Per building, keyed by its footprint's centre to the decimetre ("x,z" in model metres, z south):
  rgb   the roof's median colour from above, 0.7 m inside its walls, lifted out of the aerial's haze, linear light
  kind  for a house: "gable" or "hip", read from the roof's shading. A pitched roof shows its two long slopes in two
        tones either side of the ridge. On a gable those two tones run right to the ends; on a hip each end is one
        more slope, a single tone across the house. So the tone step across the ridge is measured in the middle
        third and again at each end: kept at the ends means gable, gone means hip. A roof whose two long slopes
        read the same tone (the sun along the ridge) tells nothing and stays a hip, the suburb's commonest.
surrounds.py reads the file when it writes buildings.bin and roofs.bin."""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "bellerive")
R = 800.0
K = 360.0 / (R * math.tan(math.radians(12.79)))    # pixels a metre in a shot


def buildings(buf):
    i = 0
    while i + 1 < len(buf):
        n = int(buf[i]); h = float(buf[i + 1])
        yield h, buf[i + 2:i + 2 + 2 * n].reshape(-1, 2).astype(float)
        i += 2 + 2 * n


def key(pts):
    c = pts.mean(axis=0)
    return "%.1f,%.1f" % (c[0], c[1])


def main(work):
    from PIL import Image, ImageDraw, ImageFilter
    C = np.array(json.load(open(os.path.join(work, "centres.json"))))   # [east, north] of each shot's centre
    shots = {}
    buf = np.fromfile(os.path.join(OUT, "buildings.bin"), "<f4")
    res = {}
    stats = {"gable": 0, "hip": 0, "flat": 0}
    for h, pts in buildings(buf):
        c = pts.mean(axis=0)
        # the nearest shot that holds the whole roof clear of Google Earth's tip box (top middle)
        found = None
        for i in np.argsort((C[:, 0] - c[0]) ** 2 + (C[:, 1] + c[1]) ** 2)[:4]:
            ce, cn = C[i]
            q = [(640 + (x - ce) * K, 360 + (z + cn) * K) for x, z in pts]
            x0, y0 = int(min(a for a, _ in q)) - 2, int(min(b for _, b in q)) - 2
            x1, y1 = int(max(a for a, _ in q)) + 3, int(max(b for _, b in q)) + 3
            if x0 < 0 or y0 < 0 or x1 > 1280 or y1 > 720 or (y0 < 64 and x1 > 650 and x0 < 1130):
                continue
            found = int(i)
            break
        if found is None:
            continue
        i = found
        if i not in shots:
            shots[i] = np.asarray(Image.open(os.path.join(work, "ge", "t%02d.png" % i)).convert("RGB")).astype(float)
        im = shots[i]
        m = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(m).polygon([(a - x0, b - y0) for a, b in q], fill=255)
        mm = np.asarray(m.filter(ImageFilter.MinFilter(3))) > 0          # 0.7 m in from the walls
        if mm.sum() < 6:
            continue
        crop = im[y0:y1, x0:x1]
        col = np.median(crop[mm], axis=0)
        col = np.clip((col - 14.0) * 1.08, 8, 255) / 255.0                 # the aerial's haze (Norwood's lift)
        entry = {"rgb": [round(float(v) ** 2.2, 4) for v in col]}
        if h < 0:
            kind = "hip"
            # the house's own axes: along its longest wall, and across
            e = [pts[(j + 1) % len(pts)] - pts[j] for j in range(len(pts))]
            ax = e[int(np.argmax([np.hypot(*d) for d in e]))]
            ax = ax / np.hypot(*ax)
            ac = np.array([-ax[1], ax[0]])
            pu, pv = (pts - c) @ ax, (pts - c) @ ac
            L, W = pu.max() - pu.min(), pv.max() - pv.min()
            um, vm = (pu.max() + pu.min()) / 2, (pv.max() + pv.min()) / 2
            yy, xx = np.nonzero(mm)
            mx = (xx + x0 - 640) / K + ce; mz = (yy + y0 - 360) / K - cn
            u = (np.c_[mx, mz] - c) @ ax - um; v = (np.c_[mx, mz] - c) @ ac - vm
            lum = (0.3 * crop[..., 0] + 0.59 * crop[..., 1] + 0.11 * crop[..., 2])[mm]
            # Facet lines: a hip's run diagonally in from each corner, a gable's only ridge runs along the
            # house. Edge strength inside the roof (1 m in from the walls) by direction against the house's axis.
            from scipy import ndimage
            g = 0.3 * crop[..., 0] + 0.59 * crop[..., 1] + 0.11 * crop[..., 2]
            gx, gy = ndimage.sobel(g, 1), ndimage.sobel(g, 0)
            inner = ndimage.binary_erosion(mm, iterations=2)
            mag = np.hypot(gx, gy)[inner]
            if inner.sum() > 20 and W > 4.0:
                ang = np.arctan2(gy[inner], gx[inner])                    # image: x east, y south = model x, z
                rel = np.abs(np.degrees(np.arctan2(np.sin(ang), np.cos(ang)) - math.atan2(ax[1], ax[0])))
                rel = np.minimum(rel % 180.0, 180.0 - rel % 180.0)        # 0 = gradient along the axis
                strong = mag > max(40.0, np.percentile(mag, 70))
                diag = (strong & (rel > 25) & (rel < 65)).sum()
                across = (strong & (rel >= 65)).sum()
                share = diag / max(1, diag + across)
                if L > 1.15 * W and across > 8 and share < 0.25:
                    kind = "gable"
                entry["tone"] = [int(diag), int(across), round(float(share), 2)]
                entry["edges"] = round(float((mag > 90).mean()), 3)
            entry["kind"] = kind
            stats[kind] += 1
        res[key(pts)] = entry
    json.dump(res, open(os.path.join(HERE, "houses_ge.json"), "w"), separators=(",", ":"))
    print(len(res), "buildings read;", stats)


if __name__ == "__main__":
    main(sys.argv[1])
