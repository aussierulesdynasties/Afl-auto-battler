"""ENGIE Stadium's ground round the stadium from OpenStreetMap (the MCG standard's stage 6, docs/MCG_STANDARD.md).

The showground's roads, car parks, lawns and arenas, Olympic Boulevard and Cathy Freeman Park, the Brickpit,
Haslams Creek's banks and the parklands to the north, painted 2 km a side at 1 m a pixel, and every tree OSM
maps there listed for the game to stand up. The buildings are not boxes from this map: each is modelled in
landmarks.py. It reuses the MCG's painter (tools/grounds/mcg/surrounds.py) with Sydney Olympic Park's place
and colours, as Bellerive's and GMHBA's do.

    python3 tools/grounds/engie/surrounds/surrounds.py [a.osm b.osm ...]

With no files it fetches the area from the OpenStreetMap API in nine tiles. Writes
assets/grounds/engie/surrounds.webp and trees.bin (the MCG's formats) in model metres: x east, z south, the
model's origin (the OSM pitch's centre) at 0, 0. Map data (c) OpenStreetMap contributors, ODbL.
"""
import json
import math
import os
import sys
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("mcg_surrounds", os.path.join(HERE, "..", "..", "mcg", "surrounds.py"))
S = importlib.util.module_from_spec(_spec)   # the MCG's painter
_spec.loader.exec_module(S)

OUT = os.path.join(HERE, "..", "..", "..", "..", "assets", "grounds", "engie")
PLAN = json.load(open(os.path.join(HERE, "..", "model", "engie.json")))
S.LAT0, S.LON0 = -33.8431119, 151.0676851
S.PITCH_E, S.PITCH_N = 0.0, 0.0
S.MODEL_R = 0.0
# Sydney Olympic Park as Google Earth shows it: dry olive lawns, pale concrete plazas, red-brown gravel at
# the Brickpit, dark eucalypt woodland along the creek.
S.BASE = (110, 118, 84)   # Olympic Park: grass under a lot of eucalypt canopy (Google Earth)
S.LAWN = (112, 124, 76)
S.PITCH = (96, 124, 66)
S.URBAN = (136, 130, 118)
S.PARKING = (112, 110, 106)
S.ASPHALT = (86, 86, 88)
S.PAVED = (172, 132, 108)   # the red-brown gravel and pavers of Olympic Boulevard and the plazas
S.ROOF = (150, 148, 142)
S.WATER = (52, 76, 80)
S.WOOD = (70, 84, 54)
DIRT = (178, 142, 104)   # the showground's equestrian rings are raked loam (Schmidt Arena, Google Earth)
_area_colour = S.area_colour


def area_colour(t):
    if t.get("leisure") in ("pitch", "track") and (t.get("sport") in ("equestrian", "horse_racing")
                                                  or t.get("surface") in ("dirt", "sand", "earth")):
        return DIRT
    return _area_colour(t)


S.area_colour = area_colour
TILES, SPAN = 3, 2400.0


def fetch(i, j, path):
    dlat = SPAN / 110574.0 / TILES
    dlon = SPAN / (111320.0 * math.cos(math.radians(S.LAT0))) / TILES
    lat0 = S.LAT0 - SPAN / 2 / 110574.0
    lon0 = S.LON0 - SPAN / 2 / (111320.0 * math.cos(math.radians(S.LAT0)))
    a, b = lon0 + i * dlon, lat0 + j * dlat
    url = "https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % (a, b, a + dlon, b + dlat)
    req = urllib.request.Request(url, headers={"User-Agent": "afl-ground-builder/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as f:
        f.write(r.read())


def canopy(ways, have):
    """Olympic Park under its real canopy (Google Earth): the street trees of OSM's tree rows (Olympic
    Boulevard's avenues, the showground's streets) one every 9 m, and OSM's woods, scrub and mangroves filled
    at one tree to 120 m2 (the MCG painter fills only lawns and parks)."""
    rng = np.random.default_rng(31)
    gap = 7.0
    cell = {}

    def free(e, n):
        k = (int(e // gap), int(n // gap))
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for qe, qn in cell.get((k[0] + i, k[1] + j), ()):
                    if (qe - e) ** 2 + (qn - n) ** 2 < gap * gap:
                        return False
        cell.setdefault(k, []).append((e, n))
        return True

    for e, n in have:
        cell.setdefault((int(e // gap), int(n // gap)), []).append((e, n))
    out = []
    for t, p in ways:
        if t.get("natural") == "tree_row" and len(p) > 1:
            for (e0, n0), (e1, n1) in zip(p, p[1:]):
                L = math.hypot(e1 - e0, n1 - n0)
                for k in range(int(L // 9.0) + 1):
                    f = k * 9.0 / L if L > 0 else 0.0
                    e, n = e0 + (e1 - e0) * f, n0 + (n1 - n0) * f
                    if free(e, n):
                        out.append((e, n))
        elif (t.get("natural") in ("wood", "scrub") or t.get("landuse") == "forest" or t.get("wetland") == "mangrove") and len(p) > 3:
            a = np.array(p, float)
            lo, hi = a.min(0), a.max(0)
            if max(np.abs(lo).max(), np.abs(hi).max()) > 1300:
                continue
            area = abs(0.5 * np.sum(a[:-1, 0] * a[1:, 1] - a[1:, 0] * a[:-1, 1]))
            want = int(area / 120.0)
            got = 0
            for _ in range(want * 6):
                if got >= want:
                    break
                e, n = lo + rng.random(2) * (hi - lo)
                inside = False
                for (x0, y0), (x1, y1) in zip(a, np.roll(a, -1, 0)):
                    if (y0 > n) != (y1 > n) and e < x0 + (n - y0) * (x1 - x0) / (y1 - y0):
                        inside = not inside
                if inside and free(e, n):
                    out.append((float(e), float(n))); got += 1
    out = [q for q in out if max(abs(v) for v in S.model_xz(*q)) < S.SIZE / 2 - 2]
    print("canopy trees", len(out))
    return out


def site_mask():
    """The stadium's own paved site (engie.json 'site', OSM way 4385854) in the map's pixels: the model draws
    everything inside it."""
    tab = PLAN['site'] + [[360, PLAN['site'][0][1]]]
    bs = np.array([b for b, _ in tab], float); rs = np.array([r for _, r in tab], float)
    yy, xx = np.mgrid[0:S.SIZE, 0:S.SIZE]
    x, z = xx - S.SIZE / 2 + 0.5, yy - S.SIZE / 2 + 0.5
    b = np.degrees(np.arctan2(x, -z)) % 360
    return np.hypot(x, z) <= np.interp(b, bs, rs) + 1.0


def main():
    paths = sys.argv[1:]
    if not paths:
        for i in range(TILES):
            for j in range(TILES):
                p = "/tmp/engie_osm_%d%d.osm" % (i, j)
                if not os.path.exists(p):
                    fetch(i, j, p)
                paths.append(p)
    trees, ways, seen = [], [], set()
    for p in paths:
        t, w = S.load(p)
        for e in t:
            if e not in seen:
                seen.add(e); trees.append(e)
        ways += w
    trees += canopy(ways, trees)
    foot = site_mask()

    def in_foot(pts):
        for q in pts:
            x, z = S.model_xz(*q)
            i, k = int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))
            if foot[i, k]:
                return True
        return False

    ways = [(t, p) for t, p in ways if not (("building" in t or t.get("leisure") in ("stadium", "pitch")) and len(p) > 2 and in_foot(p))]
    trees = [e for e in trees if not in_foot([e])]
    im, trees = S.paint(trees, ways)
    arr = np.asarray(im).copy()
    arr[foot] = (152, 149, 142)   # the concourse round the ground, as the apron paving
    Image.fromarray(arr).save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    t = S.tree_list(trees)
    keep = [not in_foot([(x, -z)]) for x, z in t[:, :2]] if len(t) else []
    t = t[keep] if len(t) else t
    t.astype("<f4").tofile(os.path.join(OUT, "trees.bin"))
    print("surrounds.webp", im.size, "trees", len(t))


if __name__ == "__main__":
    main()
