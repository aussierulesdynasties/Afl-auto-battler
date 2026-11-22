"""Manuka's town, as data for town.py: every building and tree within 1.1 km of the ground.

    python3 tools/grounds/manuka/town/prep.py      # writes $MANUKA_CACHE/town.json

Buildings: OpenStreetMap's footprints, then the ACT Government's for any it lacks. Storeys from OpenStreetMap's
building:levels, else storeys.json (read off Google Earth 3D, building by building), else by kind (a Griffith or
Forrest house is one storey; Microsoft's footprint heights, in Overture Maps, pick out the two-storey ones).
Roof colour: measured off the aerial photo inside each footprint (looking only; the photo itself is not kept)
and matched to the nearest real roofing colour (terracotta, brown and charcoal tile, Colorbond).
Trees: the ACT Government's LiDAR crowns (outline and height), each given its species from the ACT tree register
where one stands in it.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import C, CACHE, HERE, act_layer, area, latlon, load_osm, rings  # noqa: E402

R = 1100.0
MODEL_SKIP = {"122524193", "122524194", "122524195", "1290130248"}   # the stands and the scoreboard (the model)
HOUSES = ("house", "detached", "semidetached_house", "bungalow", "terrace")
SMALL = ("garage", "garages", "shed", "carport", "roof", "hut", "kiosk", "toilets", "service")

# Roofing colours (sRGB) as they read from the air in Canberra, and as built.
ROOFING = {
    "terracotta": (172, 84, 58), "red_tile": (150, 64, 50), "brown_tile": (112, 76, 62),
    "charcoal": (64, 66, 70), "grey_tile": (112, 112, 112), "colorbond_grey": (150, 152, 150),
    "zinc": (186, 188, 186), "white": (222, 222, 218), "colorbond_green": (88, 108, 92),
    "colorbond_blue": (88, 106, 126), "cream": (204, 192, 160), "black": (44, 44, 46),
}


def ortho(r=R + 60, z=18, res=0.5):
    """The aerial photo (Esri World Imagery) resampled to the frame, for measuring roof colours only."""
    import urllib.request
    from PIL import Image
    d = os.path.join(CACHE, "img18")
    os.makedirs(d, exist_ok=True)
    n = 2 ** z

    def txy(lat, lon):
        return ((lon + 180) / 360 * n, (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * n)
    la0, lo0 = latlon(-r, r)
    la1, lo1 = latlon(r, -r)
    x0, y0 = txy(la0, lo0)      # north-west corner
    x1, y1 = txy(la1, lo1)      # south-east corner
    X0, Y0 = int(x0), int(y0)
    M = np.zeros(((int(y1) - Y0 + 1) * 256, (int(x1) - X0 + 1) * 256, 3), np.uint8)
    for i in range(X0, int(x1) + 1):
        for j in range(Y0, int(y1) + 1):
            p = os.path.join(d, "%d_%d_%d.jpg" % (z, i, j))
            if not os.path.exists(p):
                urllib.request.urlretrieve("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%d/%d/%d"
                                           % (z, j, i), p)
            M[(j - Y0) * 256:(j - Y0 + 1) * 256, (i - X0) * 256:(i - X0 + 1) * 256] = np.asarray(Image.open(p).convert("RGB"))

    def sample(pts):
        pts = np.asarray(pts, float)
        lat, lon = latlon(pts[:, 0], pts[:, 1])
        x, y = txy(lat, lon)
        ix = np.clip(((x - X0) * 256).astype(int), 0, M.shape[1] - 1)
        iy = np.clip(((y - Y0) * 256).astype(int), 0, M.shape[0] - 1)
        return M[iy, ix].astype(float)
    return sample


def roof_colour(sample, ring):
    """The median colour inside the footprint, 1.2 m in from its edge, and the roofing it is nearest."""
    from shapely.geometry import Polygon
    pg = Polygon(ring)
    if not pg.is_valid:
        pg = pg.buffer(0)
    inner = pg.buffer(-1.2)
    if inner.is_empty or inner.area < 4:
        inner = pg
    x0, y0, x1, y1 = inner.bounds
    xs, ys = np.meshgrid(np.arange(x0, x1, 0.5), np.arange(y0, y1, 0.5))
    pts = np.c_[xs.ravel(), ys.ravel()]
    from shapely import contains_xy
    pts = pts[contains_xy(inner, pts[:, 0], pts[:, 1])]
    if len(pts) < 4:
        return None, None
    c = np.median(sample(pts), 0)
    # Sunlit roofs read lighter than the material; compare hue and value loosely.
    best, bd = None, 1e9
    for k, v in ROOFING.items():
        v = np.array(v, float)
        dd = np.sum((c - v) ** 2 * np.array([1.0, 1.3, 1.0]))
        if dd < bd:
            best, bd = k, dd
    return best, [int(x) for x in c]


def main():
    nodes, ways = load_osm()
    sample = ortho()
    try:
        storeys = json.load(open(os.path.join(HERE, "storeys.json")))
    except FileNotFoundError:
        storeys = {}
    ov = json.load(open(os.path.join(CACHE, "overture.json"))) if os.path.exists(os.path.join(CACHE, "overture.json")) else []
    from shapely.geometry import Polygon, Point
    from shapely.strtree import STRtree
    from common import en
    ov_polys, ov_h = [], []
    for o in ov:
        if o["height"] is None or o["g"]["type"] != "Polygon":
            continue
        ring = [en(la, lo) for lo, la in o["g"]["coordinates"][0]]
        ov_polys.append(Polygon(ring).centroid)
        ov_h.append(o["height"])
    ov_tree = STRtree(ov_polys) if ov_polys else None
    blds = []
    osm_polys = []
    for wid, t, p in ways:
        if "building" not in t or len(p) < 4 or p[0] != p[-1] or wid in MODEL_SKIP or t.get("_inner"):
            continue
        if t.get("location") == "underground" or t.get("layer", "0").startswith("-"):
            continue
        ring = p[:-1]
        c = np.mean(ring, 0)
        if math.hypot(c[0] - C[0], c[1] - C[1]) < 112 or max(abs(c[0]), abs(c[1])) > R:
            continue
        osm_polys.append(Polygon(ring))
        blds.append({"id": wid, "src": "osm", "tags": t, "ring": [list(map(float, q)) for q in ring]})
    otree = STRtree(osm_polys)
    for f in act_layer("ACTGOV_BUILDING_FOOTPRINTS"):
        if f["properties"].get("CURRENT_LIFECYCLE_STAGE") == "PROPOSED":
            continue                # not built (Griffith's community centre site is bare ground in Google Earth)
        for ring in rings(f["geometry"]):
            pg = Polygon(ring)
            if not pg.is_valid:
                pg = pg.buffer(0)
            c = pg.centroid
            if math.hypot(c.x - C[0], c.y - C[1]) < 112 or max(abs(c.x), abs(c.y)) > R:
                continue
            hit = [osm_polys[i] for i in otree.query(pg)]
            if any(h.intersection(pg).area > 0.25 * min(h.area, pg.area) for h in hit if h.is_valid):
                continue
            pr = f["properties"]
            kind = "apartments" if "APARTMENT" in (pr["USE_DESCRIPTION"] or "") else \
                "house" if pr["USE_DESCRIPTION"] == "RESIDENTIAL USE" else "yes"
            blds.append({"id": "act%d" % pr["OBJECTID"], "src": "act", "tags": {"building": kind},
                         "ring": [list(map(float, q)) for q in ring[:-1]]})
    out = []
    for b in blds:
        t = b["tags"]
        ring = b["ring"]
        a = abs(area(ring))
        if a < 6:
            continue
        kind = t.get("building", "yes")
        lv = None
        if b["id"] in storeys:
            lv = storeys[b["id"]]
        elif t.get("building:levels"):
            try:
                lv = float(str(t["building:levels"]).split(";")[0].split(",")[-1])
            except ValueError:
                lv = None
        msh = None
        if ov_tree is not None:
            pg = Polygon(ring)
            for i in ov_tree.query(pg):
                if pg.contains(ov_polys[i]):
                    msh = ov_h[i]
                    break
        roof, measured = roof_colour(sample, ring)
        small = kind in SMALL or (kind == "yes" and a < 40)
        house = kind in HOUSES or (kind in ("yes", "residential") and 40 <= a < 330 and b["src"] in ("osm", "act"))
        if isinstance(lv, dict):
            spec = lv
        else:
            spec = {}
            if lv is None:
                if small:
                    lv = 1
                elif house:
                    lv = 2 if (msh or 0) >= 5.4 else 1      # Microsoft's heights run low: 5.4 m marks a two-storey house
                else:
                    lv = 2
            spec["levels"] = lv
        spec.setdefault("roof", "flat" if (small and kind in ("carport", "roof")) else
                        "skillion" if small else "hipped" if house else "auto")
        out.append({"id": b["id"], "src": b["src"], "kind": kind, "name": t.get("name"), "ring": ring,
                    "area": a, "ms_h": msh, "roofing": roof, "roof_rgb": measured, **spec})
    # Trees: LiDAR crowns with species.
    assets = act_layer("ACTGOV_Tree_Assets", "BOTANICAL_NAME,GENUS,SPECIES,ASSET_SUB_TYPE")
    apts = []
    for f in assets:
        g = f["geometry"]
        if g and g["type"] == "Point":
            apts.append((Point(*en(g["coordinates"][1], g["coordinates"][0])), f["properties"]))
    atree = STRtree([q for q, _ in apts])
    trees = []
    for f in act_layer("ACTGOV_Mature_Trees_2020", "crownHeight,crownID"):
        for ring in rings(f["geometry"]):
            pg = Polygon(ring)
            if not pg.is_valid:
                pg = pg.buffer(0)
            c = pg.centroid
            if max(abs(c.x), abs(c.y)) > R:
                continue
            genus, bot = None, None
            for i in atree.query(pg):
                if pg.contains(apts[i][0]):
                    genus, bot = apts[i][1]["GENUS"], apts[i][1]["BOTANICAL_NAME"]
                    if genus:
                        break
            mr = pg.minimum_rotated_rectangle
            trees.append({"x": c.x, "y": c.y, "h": float(f["properties"]["crownHeight"]),
                          "r": math.sqrt(pg.area / math.pi), "genus": genus, "bot": bot,
                          "ring": [list(map(lambda v: round(v, 2), q)) for q in list(pg.exterior.coords)[:-1]][:24]})
    json.dump({"buildings": out, "trees": trees}, open(os.path.join(CACHE, "town.json"), "w"))
    import collections
    print("buildings", len(out), collections.Counter(b["src"] for b in out), "trees", len(trees))
    print(collections.Counter(b["roofing"] for b in out).most_common())
    print(collections.Counter((t["genus"] or "-") for t in trees).most_common(12))


if __name__ == "__main__":
    main()
