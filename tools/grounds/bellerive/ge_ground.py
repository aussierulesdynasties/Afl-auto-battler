"""What covers the ground round Bellerive Oval, read off the same 24 straight-down
Google Earth shots as the trees (ge_trees.py plan; 800 m, 0.5 m a pixel). Only classes, measured colours and
outlines are kept, never imagery (docs/MCG_STANDARD.md: sampled colours are fine).

  python3 ge_ground.py <workdir>     # writes ge_ground.npz + ge_ground.json beside this file

Each pixel is one of: lawn (green, smooth), dry grass (tan), bare earth or mulch (red-brown), paving or gravel
(grey), courts (near-white, flat), canopy (Adelaide's tree thresholds), or other (roofs, asphalt, shadow). They are voted onto the map's
1 m grid (each shot owns the cells nearest its centre; where the owner's tip box hid a cell, every other shot that saw
it votes). surrounds.py paints the ground in each class's own median
colour where nothing is mapped (roads, buildings, the sea and the stadium keep theirs); under the canopy and on
'other' it takes the nearest class round it.

(A pass that also turned unmapped roof-coloured blobs into buildings was tried and dropped, 2026-11-23: the maps
already hold nearly every roof, and the blobs it found were mostly bare earth, scrub and shadow.)"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import surrounds as B          # noqa: E402
S = B.S
R = 800.0
K = 360.0 / (R * math.tan(math.radians(12.79)))
HALF = S.SIZE / 2.0
NAMES = ["other", "lawn", "dry", "earth", "paving", "canopy", "court"]
MEASURED = (1, 2, 3, 4, 6)


def classify(im):
    from scipy import ndimage
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    m1 = ndimage.uniform_filter(lum, 5)
    tex = np.sqrt(np.maximum(ndimage.uniform_filter(lum * lum, 5) - m1 * m1, 0))
    sat = im.max(2) - im.min(2)
    canopy = (tex > 4) & (lum > 38) & (lum < 112) & (g - r > 8) & (g - r < 32) & (b < g + 5)
    lawn = (g - r > 6) & (g > b + 8) & ~canopy & (lum > 70)
    dry = (r >= g - 6) & (r > b + 18) & (lum >= 105) & (r - g < 22) & ~lawn
    earth = (r > g + 10) & (r > b + 25) & (lum < 150) & ~dry
    pave = (sat < 22) & (lum > 70) & (lum < 205)
    court = (sat < 26) & (lum >= 190) & (lum < 250)
    c = np.zeros(lum.shape, np.uint8)
    c[pave] = 4; c[court] = 6; c[earth] = 3; c[dry] = 2; c[lawn] = 1; c[canopy] = 5
    return c, lum


def main(work):
    from PIL import Image
    C = np.array(json.load(open(os.path.join(work, "centres.json"))))
    votes = np.zeros((S.SIZE, S.SIZE, 7), np.uint16)
    spare = np.zeros((S.SIZE, S.SIZE, 7), np.uint16)                # every shot, for cells the owner's tip box hid
    cols = {k: [] for k in MEASURED}
    rng = np.random.default_rng(3)
    for i, (ce, cn) in enumerate(C):
        f = os.path.join(work, "ge", "t%02d.png" % i)
        if not os.path.exists(f):
            print("missing", f); continue
        im = np.asarray(Image.open(f).convert("RGB")).astype(float)
        cls, lum = classify(im)
        cls[:64, 640:1140] = 255                                 # Google Earth's tip box
        ys, xs = np.nonzero(cls != 255)
        E = ce + (xs - 640) / K; N = cn - (ys - 360) / K
        own = np.argmin((E[:, None] - C[None, :, 0]) ** 2 + (N[:, None] - C[None, :, 1]) ** 2, axis=1) == i
        qx = (E + HALF).astype(int); qz = (-N + HALF).astype(int)
        ok = (qx >= 0) & (qx < S.SIZE) & (qz >= 0) & (qz < S.SIZE)
        np.add.at(spare, (qz[ok], qx[ok], cls[ys[ok], xs[ok]]), 1)
        ys, xs, E, N = ys[own], xs[own], E[own], N[own]
        px = (E + HALF).astype(int); pz = (-N + HALF).astype(int)
        ok = (px >= 0) & (px < S.SIZE) & (pz >= 0) & (pz < S.SIZE)
        ys, xs, px, pz = ys[ok], xs[ok], px[ok], pz[ok]
        k = cls[ys, xs]
        np.add.at(votes, (pz, px, k), 1)
        for c in MEASURED:
            sel = np.nonzero(k == c)[0]
            if len(sel):
                sel = rng.choice(sel, min(len(sel), 4000), replace=False)
                cols[c].append(im[ys[sel], xs[sel]])
    grid = votes.argmax(2).astype(np.uint8)
    hid = votes.sum(2) == 0
    grid[hid] = spare.argmax(2)[hid]
    grid[hid & (spare.sum(2) == 0)] = 255
    from scipy import ndimage
    court = grid == 6                                            # a court is a big flat block; small white bits
    grid[court & ~ndimage.binary_opening(court, np.ones((6, 6)))] = 4   # are cars, sheds and sun on paving
    haze = lambda c: [int(v) for v in np.clip((np.median(np.concatenate(c), 0) - 14.0) * 1.08, 0, 255)]
    colour = {NAMES[c]: haze(cols[c]) for c in MEASURED}
    np.savez_compressed(os.path.join(HERE, "ge_ground.npz"), cls=grid)
    json.dump({"names": NAMES, "colour": colour}, open(os.path.join(HERE, "ge_ground.json"), "w"),
              separators=(",", ":"))
    print("classes", {NAMES[c]: int((grid == c).sum()) for c in range(7)}, "colours", colour)


if __name__ == "__main__":
    main(sys.argv[1])
