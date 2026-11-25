"""GMHBA Stadium's surroundings from OpenStreetMap (the MCG standard's stage 6, docs/MCG_STANDARD.md).

Kardinia Park's ovals and grass, the streets of South Geelong and Geelong (Moorabool Street to the east),
the houses and the trees, painted 2 km a side at 1 m a pixel, with every building stood up and every
mapped tree listed. It reuses the MCG's painter (tools/grounds/mcg/surrounds.py) with Geelong's place,
colours and the stadium's own footprint.

    python3 tools/grounds/gmhba/surrounds.py [a.osm b.osm ...]

With no files it fetches the area from the OpenStreetMap API in four tiles. Writes
assets/grounds/gmhba/surrounds.webp, trees.bin and buildings.bin (same formats as the MCG's), in model
metres: x east, z south, the model's origin (not the field's centre) at 0, 0, as GroundModels lays the map.
Map data (c) OpenStreetMap contributors, ODbL.
"""
import math
import os
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mcg"))
import surrounds as S  # noqa: E402  (the MCG's painter)

OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "gmhba")
GLB = os.path.join(OUT, "gmhba.glb")
# The model's origin (tools/grounds/gmhba/jss_roof/measured.md: 7 Google Earth wall-foot points, rms 0.5 m).
S.LAT0, S.LON0 = -38.1579976, 144.3546774
S.PITCH_E, S.PITCH_N = 0.0, 0.0
S.MODEL_R = 0.0
# Google Earth's Geelong in late spring: Kardinia Park's grass a dry olive, the house blocks grey-brown.
S.BASE = (122, 124, 84)
S.LAWN = (104, 122, 72)
S.PITCH = (88, 122, 62)
S.URBAN = (124, 120, 106)
S.PARKING = (106, 104, 100)
S.ASPHALT = (88, 88, 88)
S.ROOF = (150, 144, 136)
TILES = [(144.3433 + i * 0.0115, -38.1670 + j * 0.009) for i in (0, 1) for j in (0, 1)]


def fetch(lon, lat, path):
    url = "https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % (lon, lat, lon + 0.0115, lat + 0.009)
    req = urllib.request.Request(url, headers={"User-Agent": "afl-ground-builder/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())


def footprint():
    """The stadium's plan (model x, z) as a 1 m mask in the map's pixels, 3 m wider all round: the model
    draws everything inside, so the map paints it plain paving and no OpenStreetMap building stands there."""
    import trimesh
    sc = trimesh.load(GLB)
    v = sc.to_geometry().vertices if hasattr(sc, "to_geometry") else sc.dump(concatenate=True).vertices
    v = v[v[:, 1] > 0.5]
    m = np.zeros((S.SIZE, S.SIZE), bool)
    ix = np.clip((v[:, 0] + S.SIZE / 2).astype(int), 0, S.SIZE - 1)
    iz = np.clip((v[:, 2] + S.SIZE / 2).astype(int), 0, S.SIZE - 1)
    m[iz, ix] = True
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
    # Close the bowl: everything inside the outermost ring of the model is the model's.
    a = np.asarray(im) > 0
    yy, xx = np.mgrid[0:S.SIZE, 0:S.SIZE]
    ang = np.arctan2(yy - S.SIZE / 2, xx - S.SIZE / 2)
    rr = np.hypot(yy - S.SIZE / 2, xx - S.SIZE / 2)
    bins = ((ang + math.pi) / (2 * math.pi) * 720).astype(int) % 720
    rmax = np.zeros(720)
    np.maximum.at(rmax, bins[a], rr[a])
    rmax = np.maximum(rmax, np.roll(rmax, 1))
    rmax = np.maximum(rmax, np.roll(rmax, -1))
    return a | (rr <= rmax[bins])


def main():
    paths = sys.argv[1:]
    if not paths:
        paths = []
        for k, (lon, lat) in enumerate(TILES):
            p = "/tmp/gmhba_osm_%d.osm" % k
            if not os.path.exists(p):
                fetch(lon, lat, p)
            paths.append(p)
    trees, ways = [], []
    seen = set()
    for p in paths:
        t, w = S.load(p)
        for e in t:
            if e not in seen:
                seen.add(e)
                trees.append(e)
        ways += w
    foot = footprint()

    def in_foot(pts, need_all=False):
        hits = [foot[int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))]
                for x, z in (S.model_xz(*q) for q in pts)]
        return all(hits) if need_all else any(hits)

    # The stadium's own OpenStreetMap buildings and pitch go: the model is the stadium.
    ways = [(t, p) for t, p in ways if not (("building" in t or t.get("leisure") in ("stadium", "pitch")) and len(p) > 2 and in_foot(p))]
    trees = [e for e in trees if not in_foot([e])]
    im, trees = S.paint(trees, ways)
    arr = np.asarray(im).copy()
    arr[foot] = (118, 116, 110)
    im = Image.fromarray(arr)
    im.save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    t = S.tree_list(trees)
    t = t[[not in_foot([(x + S.PITCH_E, -z + S.PITCH_N)]) for x, z in t[:, :2]]] if len(t) else t
    t.astype("<f4").tofile(os.path.join(OUT, "trees.bin"))
    b = building_list(ways, in_foot)
    b.tofile(os.path.join(OUT, "buildings.bin"))
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b))


def building_list(ways, in_foot):
    out = []
    for t, p in ways:
        if "building" not in t or len(p) < 4 or p[0] != p[-1] or t.get("layer", "0").startswith("-"):
            continue
        pts = [S.model_xz(*q) for q in p[:-1]]
        if in_foot(p) or max(max(abs(x), abs(z)) for x, z in pts) > 950:
            continue
        h = S.building_height(t)
        if h < 2.5:
            continue
        # Geelong's houses are single storey under a hipped roof: walls to the eaves, then the roof. A
        # negative height tells GroundModels to put a hipped roof on (untagged blocks under 400 m2 are houses).
        a = abs(S._area(np.array(pts + pts[:1])))
        if "height" not in t and "building:levels" not in t and (
                t.get("building") in ("house", "detached", "semidetached_house", "bungalow", "terrace")
                or (t.get("building") == "yes" and a < 400.0)):
            h = -3.0
        out.append(float(len(pts)))
        out.append(h)
        for x, z in pts:
            out += [x, z]
    return np.array(out, "<f4")


if __name__ == "__main__":
    main()
