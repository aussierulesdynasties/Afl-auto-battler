"""Where the trees round Adelaide Oval stand, read off Google Earth (director 2026-11-23: the surroundings come from
Google Earth, never a generic fill). Uses the straight-down shots roof_colours.py plans (about 1 px a metre):

  python3 tools/grounds/adelaide/roof_colours.py plan <workdir> && node tools/grounds/ge_shoot.js <workdir>
  python3 tools/grounds/adelaide/ge_trees.py <workdir>          (needs scipy and shapely: the bpy env has them)

A crown is darker than lawn and rougher than water, and greyer than a tree's shadow on grass (sampled 2026-11-22:
crowns lum 94-107, green 20-27 over red; shadows on grass green 35 over red; lawns lum 145+): so a pixel is canopy where
it is dark, a little rough, and green-grey but not road or water blue, and not on a mapped building, the water or a
road's own width. The canopy is cut into 7 m cells, and a cell more than
a third canopy holds one tree, placed at its canopy's middle. Writes ge_trees.json beside this file ([east, north] per
tree, metres from the model's origin); no imagery. surrounds.py plants these instead of filling parks."""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import surrounds as S          # noqa: E402
import roof_colours as R       # noqa: E402

CELL = 7.0


def main(work):
    from PIL import Image, ImageDraw
    from scipy import ndimage
    C = json.load(open(os.path.join(work, "centres.json")))
    k = R.F / R.RANGE
    _, ways = S.load("/tmp/adelaide_surrounds.osm", [p for p in (["/tmp/adelaide_cbd_%d.osm" % i for i in range(len(S.CBD_TILES))]
                                                                 + ["/tmp/adelaide_rel_%d.osm" % r for r in S.RELATIONS]) if os.path.exists(p)])
    st = S.stadium_ring(ways)
    cells = {}
    Cn = np.array(C)
    for i, (ce, cn) in enumerate(C):
        f = os.path.join(work, "ge", "t%02d.png" % i)
        if not os.path.exists(f):
            continue
        im = np.asarray(Image.open(f).convert("RGB")).astype(float)
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        lum = 0.3 * r + 0.59 * g + 0.11 * b
        m1 = ndimage.uniform_filter(lum, 5); m2 = ndimage.uniform_filter(lum * lum, 5)
        tex = np.sqrt(np.maximum(m2 - m1 * m1, 0))
        can = (tex > 4) & (lum > 38) & (lum < 112) & (g - r > 8) & (g - r < 32) & (b < g + 5)
        # what is never a crown: mapped buildings, water, roads at their width, the stadium
        no = Image.new("L", (1280, 720)); d = ImageDraw.Draw(no)
        px = lambda p: [(640 + (e - ce) * k, 360 - (n - cn) * k) for e, n in p]
        for t, p in ways:
            if len(p) < 2:
                continue
            if ("building" in t or S.area_colour(t) == S.WATER or t.get("leisure") == "stadium") and len(p) > 2:
                d.polygon(px(p), fill=1)
            elif t.get("highway") in S.WIDTH and t.get("highway") not in ("footway", "path", "cycleway", "steps"):
                d.line(px(p), fill=1, width=max(1, int(S.WIDTH[t["highway"]] * k)))
        can &= ~np.asarray(no, bool)
        can[:60, 660:1120] = False                     # Google Earth's tip box
        can = ndimage.binary_opening(can, iterations=1)
        ys, xs = np.nonzero(can)
        E = ce + (xs - 640) / k; N = cn - (ys - 360) / k
        # each pixel belongs to the shot whose centre is nearest, so the overlaps count once
        own = np.argmin((E[:, None] - Cn[None, :, 0]) ** 2 + (N[:, None] - Cn[None, :, 1]) ** 2, axis=1) == i
        E, N = E[own], N[own]
        for e, n in zip(E, N):
            key = (int(math.floor(e / CELL)), int(math.floor(n / CELL)))
            c = cells.setdefault(key, [0, 0.0, 0.0]); c[0] += 1; c[1] += e; c[2] += n
    full = CELL * CELL * k * k
    out = []
    for (cx, cy), (cnt, se, sn) in cells.items():
        if cnt < 0.35 * full:
            continue
        e, n = se / cnt, sn / cnt
        if st and S._inside((e, n), st):
            continue
        out.append([round(e, 1), round(n, 1)])
    out.sort()
    json.dump(out, open(os.path.join(HERE, "ge_trees.json"), "w"), separators=(",", ":"))
    print(len(out), "trees")


if __name__ == "__main__":
    main(sys.argv[1])
