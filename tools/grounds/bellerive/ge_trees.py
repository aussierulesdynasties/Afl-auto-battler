"""Where the trees round Bellerive Oval stand, traced off Google Earth (Adelaide's method, tools/grounds/adelaide/
ge_trees.py; director 2026-11-23: the surroundings come from Google Earth, never a generic fill).

  python3 ge_trees.py plan <workdir>          # writes <workdir>/urls.json + centres.json: 24 straight-down shots
  node ../ge_shoot.js <workdir>               #   (or the copy beside ge_compare.py) Google Earth shots
  python3 ge_trees.py trace <workdir> <osm files...>   # writes ge_trees.json beside this file

Each shot looks straight down from 800 m, 0.5 m a pixel, 646 x 363 m; the 24 tile the 2 km map. A pixel is canopy
where it is dark, a little rough and green-grey (Adelaide's thresholds), and not on a mapped building, the water, a
road at its width or the stadium. The canopy is gathered on the map's 1 m grid and cut into crowns, widest first, each as wide as the canopy
round it. Only crowns are kept ([east, north, crown radius] per tree, metres from the model's origin); no imagery is
stored or painted."""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import surrounds as B           # noqa: E402  (Bellerive's surrounds: its S is the MCG painter, set up for Bellerive)

S = B.S
R = 800.0                        # camera range, m
GE_HALF = math.tan(math.radians(12.79))   # half the 720-row crop's vertical field of view (ge_compare.py)
HALF = S.SIZE / 2.0


def plan(work):
    os.makedirs(os.path.join(work, "ge"), exist_ok=True)
    hh = R * GE_HALF
    hw = hh * 1280 / 720
    cols = int(math.ceil(S.SIZE / (2 * hw))); rows = int(math.ceil(S.SIZE / (2 * hh)))
    cs, urls = [], []
    for j in range(rows):
        for i in range(cols):
            e = -HALF + hw + i * 2 * hw
            n = HALF - hh - j * 2 * hh
            lat = S.LAT0 + n / 110574.0
            lon = S.LON0 + e / (111320.0 * math.cos(math.radians(S.LAT0)))
            urls.append([os.path.join(work, "ge", "t%02d.png" % len(cs)),
                         "https://earth.google.com/web/@%.7f,%.7f,10.0a,%.1fd,35y,0h,0t,0r" % (lat, lon, R)])
            cs.append([round(e, 2), round(n, 2)])
    json.dump(urls, open(os.path.join(work, "urls.json"), "w"))
    json.dump(cs, open(os.path.join(work, "centres.json"), "w"))
    print(len(cs), "shots planned")


def trace(work, osm):
    from PIL import Image, ImageDraw
    from scipy import ndimage
    C = json.load(open(os.path.join(work, "centres.json")))
    k = 360.0 / (R * GE_HALF)                     # pixels a metre
    ways, seen = [], set()
    for p in osm:
        for e in S.load(p)[1]:
            key = (tuple(sorted(e[0].items())), tuple(map(tuple, e[1])))
            if key not in seen:
                seen.add(key); ways.append(e)
    # What is never a crown, on the map's 1 m grid: buildings, roads at their width, the sea, the stadium.
    no = Image.new("L", (S.SIZE, S.SIZE)); d = ImageDraw.Draw(no)
    for t, p in ways:
        if len(p) < 2:
            continue
        if "building" in t and len(p) > 2:
            d.polygon([S.px(*q) for q in p], fill=1)
        elif t.get("highway") in S.WIDTH and t.get("highway") not in ("footway", "path", "cycleway", "steps"):
            d.line([S.px(*q) for q in p], fill=1, width=max(1, int(S.WIDTH[t["highway"]])))
    no = np.asarray(no, bool) | B.sea_mask(ways) | B.footprint()
    grid = np.zeros((S.SIZE, S.SIZE), bool)        # the canopy on the map's 1 m grid
    Cn = np.array(C)
    for i, (ce, cn) in enumerate(C):
        f = os.path.join(work, "ge", "t%02d.png" % i)
        if not os.path.exists(f):
            print("missing", f); continue
        im = np.asarray(Image.open(f).convert("RGB")).astype(float)
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        lum = 0.3 * r + 0.59 * g + 0.11 * b
        m1 = ndimage.uniform_filter(lum, 5); m2 = ndimage.uniform_filter(lum * lum, 5)
        tex = np.sqrt(np.maximum(m2 - m1 * m1, 0))
        can = (tex > 4) & (lum > 38) & (lum < 112) & (g - r > 8) & (g - r < 32) & (b < g + 5)
        can[:60, 660:1120] = False                 # Google Earth's tip box
        can = ndimage.binary_opening(can, iterations=1)
        ys, xs = np.nonzero(can)
        E = ce + (xs - 640) / k; N = cn - (ys - 360) / k
        own = np.argmin((E[:, None] - Cn[None, :, 0]) ** 2 + (N[:, None] - Cn[None, :, 1]) ** 2, axis=1) == i
        E, N = E[own], N[own]
        px = (E + HALF).astype(int); pz = (-N + HALF).astype(int)
        ok = (px >= 0) & (px < S.SIZE) & (pz >= 0) & (pz < S.SIZE)
        grid[pz[ok], px[ok]] = True
    grid = ndimage.binary_closing(grid, iterations=1) & ~no
    grid = ndimage.binary_opening(grid, iterations=1)
    lab, n = ndimage.label(grid)
    grid &= np.isin(lab, 1 + np.nonzero(ndimage.sum(grid, lab, range(1, n + 1)) >= 24)[0])
    # Crowns, biggest first (Bellerive's canopy-map method): each as wide as the canopy round it, the next
    # one no nearer than its crowns allow, so a big gum stays one big tree and a hedge a row of small ones.
    dist = ndimage.distance_transform_edt(grid)
    ys, xs = np.nonzero(grid)
    order = np.argsort(-dist[ys, xs], kind="stable")
    cell, out = {}, []
    for j in order:
        e, n_ = xs[j] - HALF + 0.5, HALF - ys[j] - 0.5
        rad = float(np.clip(dist[ys[j], xs[j]] * 1.3, 2.8, 7.5))
        cx, cz = int(e // 10), int(n_ // 10)
        near = [q for a in (-1, 0, 1) for c in (-1, 0, 1) for q in cell.get((cx + a, cz + c), [])]
        if any(math.hypot(qe - e, qn - n_) < max(5.0, 0.9 * (rad + qr)) for qe, qn, qr in near):
            continue
        cell.setdefault((cx, cz), []).append((e, n_, rad))
        out.append([round(e, 1), round(n_, 1), round(rad, 1)])
    out.sort()
    json.dump(out, open(os.path.join(HERE, "ge_trees.json"), "w"), separators=(",", ":"))
    print(len(out), "trees")


if __name__ == "__main__":
    if sys.argv[1] == "plan":
        plan(sys.argv[2])
    else:
        trace(sys.argv[2], sys.argv[3:])
