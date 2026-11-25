"""The coastal plain round Cazaly's as one painted map for the background scene (surr/backdrop.py): 10 km a
side at 5 m a pixel, from 1 km to 5 km out where the surroundings map (surrounds.py) has stopped. Cairns's
suburbs, the CBD's grid, the industrial estates along the Bruce Highway, Trinity Inlet's mangroves and the
cane south are painted from OpenStreetMap: land cover, every road at its width, every building's roof; the
tree canopy is laid on from Meta and WRI's canopy height map. Its alpha fades out from 4.2 to 5 km, where
the backdrop's own land colours take over.

    python3 tools/grounds/cazalys/surr/plain.py <osm dir> <chm.tif>

Writes assets/grounds/cazalys/cazalys_plain.webp (RGBA, north up, the model's origin in the middle).
Map data (c) OpenStreetMap contributors, ODbL. Canopy heights (c) Meta and World Resources Institute, CC BY 4.0.
"""
import glob, math, os, sys
import numpy as np
import osmium
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "..", "assets", "grounds", "cazalys", "cazalys_plain.webp")
LAT0, LON0 = -16.935653, 145.749062
p_ = math.radians(LAT0)
MLAT = 111132.92 - 559.82 * math.cos(2 * p_) + 1.175 * math.cos(4 * p_)
MLON = 111412.84 * math.cos(p_) - 93.5 * math.cos(3 * p_)
SPAN, N = 10240.0, 2048
RES = SPAN / N
# Colours chosen by eye against Google Earth over Cairns (2026-11-22).
BASE = (110, 118, 82)
LAND = {"residential": (118, 120, 104), "industrial": (138, 136, 128), "commercial": (136, 134, 126),
        "retail": (136, 134, 126), "farmland": (122, 132, 76), "meadow": (112, 124, 72), "grass": (104, 126, 66),
        "forest": (52, 72, 44), "cemetery": (108, 124, 72), "railway": (118, 110, 100)}
LEISURE = {"park": (100, 124, 66), "pitch": (96, 126, 62), "golf_course": (98, 130, 64), "recreation_ground": (104, 126, 66)}
WATER = (62, 96, 100)
MANGROVE = (60, 74, 50)
ROAD = (82, 82, 84)
ROOF = [(150, 150, 146), (176, 176, 170), (110, 112, 114), (150, 150, 146), (120, 96, 86), (196, 196, 190)]
WIDTH = {"motorway": 16, "trunk": 14, "primary": 13, "secondary": 11, "tertiary": 9, "residential": 7,
         "unclassified": 6, "service": 4, "living_street": 5}


def px(lon, lat):
    return ((lon - LON0) * MLON / RES + N / 2, N / 2 - (lat - LAT0) * MLAT / RES)


class H(osmium.SimpleHandler):
    def __init__(s):
        super().__init__(); s.areas = []; s.roads = []; s.bld = []; s.seen = set()

    def way(s, w):
        if w.id in s.seen:
            return
        s.seen.add(w.id)
        try:
            pts = [(n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        t = {x.k: x.v for x in w.tags}
        closed = len(pts) > 3 and w.nodes[0].ref == w.nodes[-1].ref
        if "building" in t and closed:
            s.bld.append(pts)
        elif t.get("highway") in WIDTH:
            s.roads.append((WIDTH[t["highway"]], pts))
        elif closed:
            s.areas.append((t, pts))


def colour(t):
    if t.get("natural") == "water" or t.get("waterway") == "riverbank":
        return WATER
    if t.get("natural") == "wetland":
        return MANGROVE
    if t.get("natural") in ("wood", "scrub"):
        return LAND["forest"] if t["natural"] == "wood" else (96, 108, 66)
    if t.get("leisure") in LEISURE:
        return LEISURE[t["leisure"]]
    if t.get("amenity") == "parking":
        return (104, 104, 102)
    return LAND.get(t.get("landuse"))


def main():
    h = H()
    for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.osm"))):
        h.apply_file(f, locations=True)
    rng = np.random.default_rng(3)
    n1 = np.asarray(Image.fromarray((rng.random((128, 128)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC), float) / 255
    base = np.array(BASE, float)[None, None] * (0.9 + 0.2 * n1[..., None])
    im = Image.fromarray(base.astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    # Big areas first, so small parks and ponds land on top of the suburb they sit in.
    def area(pts):
        a = np.array([px(*q) for q in pts]); return abs(np.sum(a[:-1, 0] * a[1:, 1] - a[1:, 0] * a[:-1, 1])) / 2
    for t, pts in sorted(h.areas, key=lambda tp: -area(tp[1])):
        c = colour(t)
        if c:
            d.polygon([px(*q) for q in pts], fill=c)
    arr = np.asarray(im).astype(float)
    # Canopy: Meta / WRI heights, resampled to 5 m.
    import rasterio
    from rasterio.windows import from_bounds
    r = rasterio.open(sys.argv[2])
    R = 6378137.0
    mx = math.radians(LON0) * R; my = R * math.log(math.tan(math.pi / 4 + math.radians(LAT0) / 2))
    k = 1 / math.cos(math.radians(LAT0)); half = SPAN / 2 * k
    chm = r.read(1, window=from_bounds(mx - half, my - half, mx + half, my + half, r.transform), out_shape=(N, N),
                 resampling=rasterio.enums.Resampling.average).astype(float)
    cov = np.clip((chm - 1.5) / 6.0, 0, 1)[..., None]
    tree = np.array([62, 84, 48], float) * (0.85 + 0.3 * n1[..., None])
    arr = arr * (1 - 0.85 * cov) + tree * 0.85 * cov
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for w, pts in h.roads:
        d.line([px(*q) for q in pts], fill=ROAD, width=max(1, int(round(w / RES))))
    for i, pts in enumerate(h.bld):
        d.polygon([px(*q) for q in pts], fill=ROOF[i % len(ROOF)])
    a = np.asarray(im)
    yy, xx = np.mgrid[0:N, 0:N]
    rr = np.hypot(xx - N / 2 + 0.5, yy - N / 2 + 0.5) * RES
    alpha = (np.clip((5000.0 - rr) / 800.0, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(np.dstack([a, alpha]), "RGBA").save(OUT, quality=90, method=6)
    print("plain", OUT, "areas", len(h.areas), "roads", len(h.roads), "buildings", len(h.bld))


if __name__ == "__main__":
    main()
