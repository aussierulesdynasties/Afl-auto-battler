"""What covers the ground round Bellerive Oval, read off straight-down Google Earth shots (ge_trees.py plan; 800 m,
0.5 m a pixel: the 24 the trees came from, and 24 more 181 m north of them, which see the strips Google Earth's tip
box hides in the first). Only classes, measured colours and outlines are kept, never imagery (docs/MCG_STANDARD.md:
sampled colours are fine).

  python3 ge_ground.py <workdir> [<workdir> ...]     # writes ge_ground.npz + ge_ground.json beside this file

Each pixel is one of: lawn (green, smooth), dry grass (tan), bare earth or mulch (red-brown), paving, tar or gravel
(grey), courts (near-white, flat), canopy (Adelaide's tree thresholds), or other (roofs, shadow). They are voted onto
the map's 1 m grid and onto a 0.375 m grid 768 m a side round the ground (the near map, surrounds_near.webp): each
shot owns the cells nearest its centre; where the owner's tip box hid a cell, every other shot that saw it votes.
surrounds.py paints the ground in each class's own median colour where nothing is mapped (roads, buildings, the sea
and the stadium keep theirs); under the canopy and on 'other' it takes the nearest class round it, and the trees
fill the canopy (surrounds.canopy_trees).

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
NAMES = ["other", "lawn", "dry", "earth", "paving", "canopy", "court", "field"]
MEASURED = (1, 2, 3, 4, 6, 7)
NC = len(NAMES)
# The fine grid close to the ground (surrounds_near.webp): FINE_SPAN m a side at FINE_STEP m a cell, Google
# Earth's own 0.5 m shots voted straight onto it.
FINE_SPAN = 768.0
FINE_N = 2048
FINE_STEP = FINE_SPAN / FINE_N


def classify(im):
    from scipy import ndimage
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    m1 = ndimage.uniform_filter(lum, 5)
    tex = np.sqrt(np.maximum(ndimage.uniform_filter(lum * lum, 5) - m1 * m1, 0))
    sat = im.max(2) - im.min(2)
    canopy = (tex > 4) & (lum > 38) & (lum < 112) & (g - r > 8) & (g - r < 32) & (b < g + 5)
    # Lawn and dry grass down into the shade of a yard (PC check r5: with lawn above 70 and dry grass above 105,
    # most yards fell to 'other' and took the paving beside them: a beige wash with no lawns)
    lawn = (g - r > 4) & (g > b + 4) & ~canopy & (lum > 50)
    dry = (r >= g - 8) & (r > b + 12) & (lum >= 70) & (r - g < 24) & ~lawn
    earth = (r > g + 10) & (r > b + 25) & (lum < 150) & ~dry
    pave = (sat < 22) & (lum > 70) & (lum < 205)                  # Bellerive's tar reads here too, in the sun
    court = (sat < 26) & (lum >= 190) & (lum < 250)
    c = np.zeros(lum.shape, np.uint8)
    # Sunlit open grass (sports fields, the park, the oval's banks) apart from a yard's lawn: one median for both
    # read the fields as a yard's grey-green (PC check r5: the east fields missing; GE fields 146,168,122)
    field = lawn & (lum >= 125) & (g - b > 20)
    c[pave] = 4; c[court] = 6; c[earth] = 3; c[dry] = 2; c[lawn] = 1; c[field] = 7; c[canopy] = 5
    return c, lum


def main(works):
    from PIL import Image
    shots = []                                   # (picture, its centre east, north) from every workdir
    for work in works:
        for i, c in enumerate(json.load(open(os.path.join(work, "centres.json")))):
            shots.append((os.path.join(work, "ge", "t%02d.png" % i), c))
    shots = [(f, c) for f, c in shots if os.path.exists(f) or print("missing", f)]
    C = np.array([c for _, c in shots])
    votes = np.zeros((S.SIZE, S.SIZE, NC), np.uint16)
    fine = np.zeros((FINE_N, FINE_N, NC), np.uint8)
    spare = np.zeros((S.SIZE, S.SIZE, NC), np.uint16)                # every shot, for cells the owner's tip box hid
    cols = {k: [] for k in MEASURED}
    rng = np.random.default_rng(3)
    for i, (f, (ce, cn)) in enumerate(shots):
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
        fx = ((E[ok] + FINE_SPAN / 2) / FINE_STEP).astype(int); fz = ((-N[ok] + FINE_SPAN / 2) / FINE_STEP).astype(int)
        f_ok = (fx >= 0) & (fx < FINE_N) & (fz >= 0) & (fz < FINE_N)
        fv = np.zeros((FINE_N, FINE_N, NC), np.uint16)
        np.add.at(fv, (fz[f_ok], fx[f_ok], k[f_ok]), 1)
        fine = np.minimum(fine.astype(np.uint16) + fv, 255).astype(np.uint8)
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
    # A court is a big flat block; small white bits are cars, sheds and sun on paving. Its lines and the grass
    # through its surface are holes to fill first (PC check r5: the east court was opened away to paving).
    court = ndimage.binary_fill_holes(ndimage.binary_closing(grid == 6, np.ones((3, 3))))
    grid[court] = 6
    grid[(grid == 6) & ~ndimage.binary_opening(court, np.ones((6, 6)))] = 4   # are cars, sheds and sun on paving
    # The fine grid: each cell the class most shots' pixels in it say; a cell no pixel landed in (0.375 m cells
    # under 0.5 m pixels) or the tip box hid takes the nearest that has one, then the 1 m grid's where none is near.
    fg = fine.argmax(2).astype(np.uint8)
    empty = fine.sum(2) == 0
    _, (ii, jj) = ndimage.distance_transform_edt(empty, return_indices=True)
    far = ndimage.distance_transform_edt(empty) * FINE_STEP > 3.0
    fg = fg[ii, jj]
    yy, xx = np.mgrid[0:FINE_N, 0:FINE_N]
    gx = np.clip(((xx + 0.5) * FINE_STEP - FINE_SPAN / 2 + HALF).astype(int), 0, S.SIZE - 1)
    gz = np.clip(((yy + 0.5) * FINE_STEP - FINE_SPAN / 2 + HALF).astype(int), 0, S.SIZE - 1)
    fg[far] = grid[gz, gx][far]
    fc = ndimage.binary_fill_holes(ndimage.binary_closing(fg == 6, np.ones((7, 7))))
    fg[fc] = 6
    fg[(fg == 6) & ~ndimage.binary_opening(fc, np.ones((16, 16)))] = 4
    haze = lambda c: [int(v) for v in np.clip((np.median(np.concatenate(c), 0) - 14.0) * 1.08, 0, 255)]
    colour = {NAMES[c]: haze(cols[c]) for c in MEASURED}
    np.savez_compressed(os.path.join(HERE, "ge_ground.npz"), cls=grid, fine=fg)
    json.dump({"names": NAMES, "colour": colour, "fine_span": FINE_SPAN}, open(os.path.join(HERE, "ge_ground.json"), "w"),
              separators=(",", ":"))
    print("classes", {NAMES[c]: int((grid == c).sum()) for c in range(NC)}, "colours", colour)


if __name__ == "__main__":
    main(sys.argv[1:])
