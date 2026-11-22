"""Paddington's trees: the street and backyard canopy of the streets of houses round the SCG (SCG rebuild, 2026-11-22).

OpenStreetMap maps the park trees round the SCG (tools/grounds/scg/surrounds.py) but almost none of the
plane trees along Paddington's streets or the trees in its backyards, so the streets of terraces north of
the ground read bare. Google Earth shows Paddington under a near-continuous canopy, the other streets of
houses (Surry Hills, Moore Park, Kensington) under a thinner one. This scatters trees over the map's
streets of houses (its URBAN colour), clear of buildings and of the trees already there:

- Paddington (north of the ground, x > PADD_X0, z < PADD_Z1): one tree per PADD_DENSITY square metres;
- the other streets of houses: one per OTHER_DENSITY;
- 7-14 m high, crowns 0.4-0.55 of the height, never within GAP metres of another tree.

    python3 tools/grounds/scg/paddington.py

The first run keeps the mapped trees in tools/grounds/scg/trees_mapped.bin and reads them from there
afterwards, so running it again gives the same trees.bin. Model metres: x east, z south.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg")
MAPPED = os.path.join(ROOT, "trees_mapped.bin")
SIZE = 2048
URBAN = np.array([150, 150, 128])
PC = np.array([0.94, 11.82])
MODEL_R = 190.0           # nothing inside the stadium's own footprint and forecourt
REACH = 980.0
PADD_X0, PADD_Z1 = -380.0, -170.0
PADD_DENSITY = 1.0 / 260.0
OTHER_DENSITY = 1.0 / 900.0
GAP = 7.0


def footprints():
    out = []
    for f, skip in ((os.path.join(DIR, "buildings.bin"), 0), (os.path.join(ROOT, "near_buildings.bin"), 1)):
        if not os.path.exists(f):
            continue
        b = np.fromfile(f, "<f4")
        i = 0
        while i < len(b):
            i += skip
            n = int(b[i])
            out.append(b[i + 2:i + 2 + 2 * n].reshape(-1, 2))
            i += 2 + 2 * n
    return out


def main():
    if not os.path.exists(MAPPED):
        np.fromfile(os.path.join(DIR, "trees.bin"), "<f4").tofile(MAPPED)
    have = np.fromfile(MAPPED, "<f4").reshape(-1, 5)
    im = np.asarray(Image.open(os.path.join(DIR, "surrounds.webp")).convert("RGB")).astype(int)
    urban = np.abs(im - URBAN[None, None, :]).sum(-1) < 14
    # keep off the buildings, with a metre's margin, and off the edges of the urban areas (roads)
    blk = Image.new("L", (SIZE, SIZE), 0)
    d = ImageDraw.Draw(blk)
    for p in footprints():
        if len(p) > 2:
            d.polygon([(float(x) + SIZE / 2, float(z) + SIZE / 2) for x, z in p], fill=255)
    blk = np.asarray(blk.filter(ImageFilter.MaxFilter(3))) > 0
    ok = urban & ~blk
    ok = np.asarray(Image.fromarray((~ok * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) == 0
    zs, xs = np.nonzero(ok)
    x = xs - SIZE / 2 + 0.5
    z = zs - SIZE / 2 + 0.5
    r = np.hypot(x - PC[0], z - PC[1])
    keep = (r > MODEL_R) & (np.maximum(np.abs(x), np.abs(z)) < REACH)
    x, z = x[keep], z[keep]
    padd = (x > PADD_X0) & (z < PADD_Z1)
    rng = np.random.default_rng(47)
    cell = {}

    def key(a, b):
        return (int(a // GAP), int(b // GAP))

    for a, b in have[:, :2]:
        cell.setdefault(key(a, b), []).append((a, b))
    added = []
    for sel, dens in ((padd, PADD_DENSITY), (~padd, OTHER_DENSITY)):
        cx, cz = x[sel], z[sel]
        want = int(len(cx) * dens)
        order = rng.permutation(len(cx))
        got = 0
        for k in order:
            if got >= want:
                break
            a, b = cx[k] + rng.random() - 0.5, cz[k] + rng.random() - 0.5
            i, j = key(a, b)
            if any(math.hypot(a - p, b - q) < GAP for di in (-1, 0, 1) for dj in (-1, 0, 1) for p, q in cell.get((i + di, j + dj), [])):
                continue
            h = float(rng.uniform(7.0, 14.0))
            added.append((a, b, h, h * float(rng.uniform(0.4, 0.55)), float(rng.uniform(0.75, 1.0))))
            cell.setdefault((i, j), []).append((a, b))
            got += 1
    out = np.concatenate([have, np.array(added, "<f4").reshape(-1, 5)])
    out.astype("<f4").tofile(os.path.join(DIR, "trees.bin"))
    print("trees: %d mapped + %d in the streets of houses (%d in Paddington) = %d" % (
        len(have), len(added), sum(1 for t in added if t[0] > PADD_X0 and t[1] < PADD_Z1), len(out)))


if __name__ == "__main__":
    main()
