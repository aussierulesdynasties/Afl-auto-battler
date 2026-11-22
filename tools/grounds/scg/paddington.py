"""Paddington's trees: the street and backyard canopy of the streets of houses round the SCG (SCG rebuild, 2026-11-22).

OpenStreetMap maps the park trees round the SCG (tools/grounds/scg/surrounds.py) but almost none of the
plane trees along Paddington's streets or the trees in its backyards, so the streets of terraces north of
the ground read bare. Google Earth shows Paddington under a near-continuous canopy, the other streets of
houses (Surry Hills, Moore Park, Kensington) under a thinner one. This scatters trees over the map's
streets of houses (its URBAN colour), clear of buildings and of the trees already there:

- Paddington (north of the ground, x > PADD_X0, z < PADD_Z1): one tree per PADD_DENSITY square metres;
- the other streets of houses: one per OTHER_DENSITY;
- 7-14 m high, crowns 0.4-0.55 of the height, never within GAP metres of another tree;
- before those, street trees: one every STREET_GAP metres along both verges of every street,
  10-18 m, where the verge is open ground, as Google Earth shows the streets round the ground lined;
- and first of all, the canopy Google Earth shows within about 350 m of the ground (canopy_ge.png, traced by
  canopy.py): the figs and gums of the Entertainment Quarter, Disney Studios' lot and Driver Avenue that
  OpenStreetMap leaves out, a tree every GAP metres through each patch of canopy, 11-20 m high.

    python3 tools/grounds/scg/paddington.py

The first run after surrounds.py keeps the mapped trees in tools/grounds/scg/trees_mapped.bin and reads
them from there afterwards, so running it again gives the same trees.bin. Model metres: x east, z south.
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
CANOPY = os.path.join(ROOT, "canopy_ge.png")
CANOPY_R = 130.0          # the canopy mask's trees stop at the stands' backs
STREET_GAP = 13.0         # metres between street trees
VERGE = 2.5               # metres from the kerb to the trunk
STREET_WIDTH = {"trunk": 14, "primary": 13, "secondary": 11, "tertiary": 9, "residential": 7,
                "unclassified": 6, "living_street": 5}      # surrounds.py's widths
ROAD = np.array([140, 134, 124])                             # surrounds.py's ASPHALT


def streets():
    """Each street's segments (model x, z) and half its width, from the OpenStreetMap tiles surrounds.py
    fetched (/tmp/scg_surrounds_*.osm)."""
    import glob
    import xml.etree.ElementTree as ET
    lat0, lon0 = -33.8916, 151.2248
    kx, ky = 111320.0 * math.cos(math.radians(lat0)), 110574.0
    nodes, out, seen = {}, [], set()
    files = sorted(glob.glob("/tmp/scg_surrounds_*.osm"))
    roots = [ET.parse(f).getroot() for f in files]
    for r in roots:
        for n in r.findall("node"):
            nodes[n.get("id")] = ((float(n.get("lon")) - lon0) * kx, -(float(n.get("lat")) - lat0) * ky)
    for r in roots:
        for w in r.findall("way"):
            t = {x.get("k"): x.get("v") for x in w.findall("tag")}
            hw = t.get("highway")
            if hw not in STREET_WIDTH or w.get("id") in seen or t.get("tunnel") == "yes" or t.get("bridge") == "yes":
                continue
            seen.add(w.get("id"))
            p = [nodes[x.get("ref")] for x in w.findall("nd") if x.get("ref") in nodes]
            out += [(p[k], p[k + 1], STREET_WIDTH[hw] / 2) for k in range(len(p) - 1)]
    return out


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
    import json
    f = os.path.join(ROOT, "unmapped.json")       # the buildings traced from Google Earth (facades.py)
    if os.path.exists(f):
        out += [np.array(e["footprint"]) for e in json.load(open(f))]
    return out


def main():
    now = np.fromfile(os.path.join(DIR, "trees.bin"), "<f4")
    if not os.path.exists(MAPPED) or len(now) <= os.path.getsize(MAPPED) // 4:
        now.tofile(MAPPED)          # a fresh trees.bin from surrounds.py: the mapped trees
    have = np.fromfile(MAPPED, "<f4").reshape(-1, 5)
    im = np.asarray(Image.open(os.path.join(DIR, "surrounds.webp")).convert("RGB")).astype(int)
    # the map's grain lifts all three channels alike: match the hue tightly and the brightness loosely,
    # so the paved plazas, close to URBAN in brightness, are told apart by their hue
    hue = im - im.mean(-1, keepdims=True)
    urban = (np.abs(hue - (URBAN - URBAN.mean())[None, None, :]).sum(-1) < 8) & (np.abs(im.mean(-1) - URBAN.mean()) < 25)
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
    road = (np.abs(hue - (ROAD - ROAD.mean())[None, None, :]).sum(-1) < 6) & (np.abs(im.mean(-1) - ROAD.mean()) < 8)

    def free(a, b):
        i, j = key(a, b)
        return not any(math.hypot(a - p, b - q) < GAP for di in (-1, 0, 1) for dj in (-1, 0, 1)
                       for p, q in cell.get((i + di, j + dj), []))

    # Google Earth's canopy first: every pixel of it in random order, a tree wherever none stands within GAP
    if os.path.exists(CANOPY):
        cm = np.asarray(Image.open(CANOPY).convert("L")) > 0
        # never on a playing field (the Showring is open grass; its dark patches traced as canopy)
        field = np.abs(im - np.array([112, 146, 70])[None, None, :]).sum(-1) < 40     # surrounds.py's PITCH
        cz, cx = np.nonzero(cm & ~blk & ~road & ~field)
        for k in rng.permutation(len(cx)):
            a, b = cx[k] - SIZE / 2 + float(rng.random()), cz[k] - SIZE / 2 + float(rng.random())
            if math.hypot(a - PC[0], b - PC[1]) < CANOPY_R or not free(a, b):
                continue
            h = float(rng.uniform(11.0, 20.0))
            added.append((a, b, h, h * float(rng.uniform(0.45, 0.6)), float(rng.uniform(0.7, 1.0))))
            cell.setdefault(key(a, b), []).append((a, b))
    n_canopy = len(added)
    # street trees next: Google Earth shows the streets round the ground lined both sides (Moreton Bay
    # figs on Moore Park Road, Driver Avenue and Anzac Parade, planes through Paddington), which
    # OpenStreetMap maps only in places. One every STREET_GAP metres along each street's verge, where the
    # verge is open ground (not a building, not road).
    for (ax, az), (bx, bz), half in streets():
        L = math.hypot(bx - ax, bz - az)
        if L < 1.0:
            continue
        tx, tz = (bx - ax) / L, (bz - az) / L
        for side in (-1.0, 1.0):
            off = half + VERGE
            ox, oz = -tz * off * side, tx * off * side
            t = float(rng.uniform(0, STREET_GAP))
            while t < L:
                a, b = ax + tx * t + ox, az + tz * t + oz
                t += STREET_GAP * float(rng.uniform(0.8, 1.2))
                if math.hypot(a - PC[0], b - PC[1]) < MODEL_R or max(abs(a), abs(b)) > REACH:
                    continue
                pxx, pzz = int(a + SIZE / 2), int(b + SIZE / 2)
                if blk[pzz, pxx] or road[pzz, pxx]:
                    continue
                i, j = key(a, b)
                if any(math.hypot(a - p, b - q) < GAP for di in (-1, 0, 1) for dj in (-1, 0, 1) for p, q in cell.get((i + di, j + dj), [])):
                    continue
                h = float(rng.uniform(10.0, 18.0))
                added.append((a, b, h, h * float(rng.uniform(0.42, 0.58)), float(rng.uniform(0.75, 1.0))))
                cell.setdefault((i, j), []).append((a, b))
    n_street = len(added) - n_canopy
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
    print("trees: %d mapped + %d from Google Earth's canopy + %d along streets + %d in the streets of houses = %d" % (
        len(have), n_canopy, n_street, len(added) - n_street - n_canopy, len(out)))


if __name__ == "__main__":
    main()
