"""Manuka's ground from OpenStreetMap, painted 2.2 km a side (4096 px, 0.54 m a pixel) for town.py to drape
over the land: the streets with their kerbs and lane lines, the car parks with their bays, the footpaths
and cycleways, Telopea Park's dry grass and the watered ovals, the school grounds, the pools and the
courts, every garden's lawn, and under each LiDAR tree crown its shade.

    python3 tools/grounds/manuka/town/groundmap.py      # writes $MANUKA_CACHE/groundmap.png

Colours are Google Earth's Canberra in summer, read by eye; nothing is copied from imagery.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, act_layer, area, load_osm, rings  # noqa: E402

R = 1100.0
SIZE = 4096
PPM = SIZE / (2 * R)          # pixels a metre

DRY = (178, 156, 112)          # unwatered parkland, Telopea Park and the verges in summer
LAWN = (150, 142, 98)          # the gardens' mixed lawns and beds, dry in summer as Google Earth shows them
GREEN = (104, 138, 70)          # watered ovals and school fields
WOOD = (96, 104, 70)
ASPHALT = (94, 96, 100)
ASPHALT_MAJOR = (84, 86, 90)
KERB = (176, 174, 166)
CONCRETE = (196, 190, 178)
PAVED = (160, 156, 148)
GRAVEL = (170, 154, 128)
PARKING = (104, 104, 106)
LINE = (228, 228, 222)
POOL = (70, 158, 190)
POND = (74, 98, 92)
COURT = (92, 102, 98)          # Canberra's public courts: worn grey-green asphalt
COURT_BLUE = (52, 96, 140)
SAND = (206, 186, 146)
UNDER = (112, 110, 104)        # under a building's footprint (its roof covers it)

ROADS = {"motorway": 15.0, "trunk": 10.5, "primary": 10.0, "secondary": 9.0, "tertiary": 8.0,
         "motorway_link": 6.5, "trunk_link": 6.5, "primary_link": 6.5, "secondary_link": 6.5, "tertiary_link": 6.0,
         "residential": 7.2, "unclassified": 6.5, "living_street": 5.5, "service": 4.5}
PATHS = {"footway": 1.6, "path": 1.4, "cycleway": 2.5, "pedestrian": 4.0, "steps": 2.0, "track": 2.8}


def px(p):
    return ((p[0] + R) * PPM, (R - p[1]) * PPM)


def poly(pts):
    return [px(p) for p in pts]


def area_fill(t):
    if t.get("_inner"):
        return None
    lu, le, am, na = t.get("landuse"), t.get("leisure"), t.get("amenity"), t.get("natural")
    if le == "swimming_pool":
        return POOL
    if le == "sports_centre":
        return GREEN
    if na == "water" or lu in ("reservoir", "basin") or t.get("man_made") == "pond":
        return POND
    if le == "pitch":
        sport = t.get("sport", "")
        if sport in ("tennis", "basketball", "netball", "handball", "table_tennis"):
            return COURT_BLUE if t.get("surface") == "acrylic" else COURT
        if sport == "cricket_nets":
            return GREEN
        return GREEN
    if t.get("leisure") == "playground":
        return SAND
    if am == "parking" and t.get("parking") not in ("underground", "multi-storey"):
        return PARKING
    if na == "wood" or lu == "forest":
        return WOOD
    if le in ("park", "garden", "recreation_ground", "common") or lu in ("grass", "recreation_ground", "village_green",
                                                                          "greenfield", "meadow"):
        return GREEN if t.get("irrigated") == "yes" else DRY
    if lu in ("residential",):
        return LAWN
    if am in ("school", "kindergarten", "college", "place_of_worship") or lu == "religious":
        return DRY
    if lu in ("commercial", "retail", "industrial", "construction") or t.get("area:highway") or \
            (t.get("highway") == "pedestrian" and t.get("area") == "yes"):
        return PAVED
    if t.get("surface") in ("concrete", "paving_stones", "paved") and t.get("area") == "yes":
        return CONCRETE
    return None


def dashes(d, pts, on, off, width, fill):
    """A dashed line along pts, on/off in metres."""
    acc, draw = 0.0, True
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        s = 0.0
        while s < L:
            seg = (on if draw else off) - acc
            e = min(L, s + seg)
            if draw:
                p0 = (a[0] + (b[0] - a[0]) * s / L, a[1] + (b[1] - a[1]) * s / L)
                p1 = (a[0] + (b[0] - a[0]) * e / L, a[1] + (b[1] - a[1]) * e / L)
                d.line([px(p0), px(p1)], fill=fill, width=width)
            acc += e - s
            s = e
            if acc >= (on if draw else off) - 1e-6:
                acc, draw = 0.0, not draw


def offset(pts, o):
    """pts moved o m to their left (a lane line)."""
    out = []
    P = np.asarray(pts, float)
    for i in range(len(P)):
        a, b = P[max(i - 1, 0)], P[min(i + 1, len(P) - 1)]
        t = b - a
        L = np.hypot(*t) or 1.0
        out.append((P[i][0] - t[1] / L * o, P[i][1] + t[0] / L * o))
    return out


def parking_bays(d, pts):
    """White bay lines across a parking aisle, both sides, every 2.6 m."""
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = np.asarray(a), np.asarray(b)
        L = float(np.hypot(*(b - a)))
        if L < 3:
            continue
        t = (b - a) / L
        nrm = np.array([-t[1], t[0]])
        for s in np.arange(1.3, L - 1.0, 2.6):
            c = a + t * s
            for side in (1, -1):
                p0 = c + nrm * side * 3.2
                p1 = c + nrm * side * 8.2
                d.line([px(p0), px(p1)], fill=LINE, width=1)


def paint(crowns):
    nodes, ways = load_osm()
    rng = np.random.default_rng(1929)
    def noise(n):
        return np.asarray(Image.fromarray((rng.random((n, n)) * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC),
                          np.float32) / 255 - 0.5
    mott = noise(48) * 0.18 + noise(220) * 0.12 + noise(900) * 0.08
    im = Image.new("RGB", (SIZE, SIZE), LAWN)   # unmapped land is gardens and verges
    d = ImageDraw.Draw(im)
    areas = [(t, p) for w, t, p in ways if len(p) > 2 and p[0] == p[-1] and area_fill(t)]
    areas.sort(key=lambda a: -abs(area(a[1])))
    for t, p in areas:
        d.polygon(poly(p), fill=area_fill(t))
        if t.get("leisure") == "swimming_pool":
            d.line(poly(p), fill=CONCRETE, width=max(1, int(PPM * 0.6)))
    for w, t, p in ways:          # holes in multipolygons go back to dry grass
        if t.get("_inner") and len(p) > 2:
            d.polygon(poly(p), fill=DRY)
    arr = np.asarray(im, np.float32)
    lawnish = (np.abs(arr - np.array(LAWN)).sum(-1) < 6)
    # Gardens: lawns in patches green and straw, beds darker.
    g = noise(160)
    arr[lawnish] = (np.array(LAWN) * (1 + mott[lawnish, None])
                    + np.where(g[lawnish, None] > 0.1, np.array([-40, -14, -30]), 0)
                    + np.where(g[lawnish, None] < -0.15, np.array([30, 22, 14]), 0))
    dry = (np.abs(arr - np.array(DRY)).sum(-1) < 6)
    arr[dry] = np.array(DRY) * (1 + mott[dry, None] * 1.2)
    grn = (np.abs(arr - np.array(GREEN)).sum(-1) < 6)
    arr[grn] = np.array(GREEN) * (1 + mott[grn, None] * 0.6)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # Sports pitches' lines and courts' lines.
    for w, t, p in ways:
        if t.get("leisure") == "pitch" and len(p) > 3 and t.get("sport") in ("tennis", "basketball", "netball"):
            d.line(poly(p), fill=LINE, width=max(1, int(PPM * 0.1)))
    # Paths under the roads.
    for w, t, p in ways:
        hw = t.get("highway")
        if hw in PATHS and len(p) > 1 and t.get("area") != "yes" and t.get("tunnel") != "yes":
            surf = t.get("surface", "concrete")
            fill = ASPHALT if surf == "asphalt" and hw == "cycleway" else GRAVEL if surf in ("gravel", "ground", "dirt", "unpaved", "fine_gravel") else CONCRETE
            d.line(poly(p), fill=fill, width=max(1, int(round(PATHS[hw] * PPM))), joint="curve")
    roads = sorted([(ROADS[t["highway"]], t, p) for w, t, p in ways if t.get("highway") in ROADS and len(p) > 1
                    and t.get("tunnel") != "yes" and t.get("area") != "yes"], key=lambda a: a[0])
    for wd, t, p in roads:     # kerbs first, all of them, so a junction has no kerb across it
        if t.get("highway") == "service" and t.get("service") in ("parking_aisle", "driveway"):
            continue
        d.line(poly(p), fill=KERB, width=int(round((wd + 0.8) * PPM)), joint="curve")
    for wd, t, p in roads:
        fill = ASPHALT_MAJOR if wd >= 9 else PARKING if t.get("service") == "parking_aisle" else ASPHALT
        wd = wd if t.get("service") != "parking_aisle" else 6.0
        d.line(poly(p), fill=fill, width=int(round(wd * PPM)), joint="curve")
        for q in (p[0], p[-1]):   # round the ends so a cul-de-sac reads as one
            x, y = px(q)
            rr = wd * PPM / 2
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=fill)
    for wd, t, p in roads:
        hw = t.get("highway")
        if t.get("service") == "parking_aisle":
            parking_bays(d, p)
            continue
        if hw in ("residential", "service", "unclassified", "living_street"):
            continue
        lanes = int(t.get("lanes", "2" if t.get("oneway") != "yes" else "1") or 2)
        lw = wd / max(lanes, 1)
        if t.get("oneway") == "yes":
            for k in range(1, lanes):
                dashes(d, offset(p, -wd / 2 + k * lw), 3.0, 9.0, max(1, int(PPM * 0.12)), LINE)
            d.line(poly(offset(p, wd / 2 - 0.4)), fill=LINE, width=1)
            d.line(poly(offset(p, -wd / 2 + 0.4)), fill=LINE, width=1)
        else:
            dashes(d, p, 3.0, 9.0, max(1, int(PPM * 0.12)), LINE)
    # Crossings and stop lines from the mapped crossing nodes.
    for nid, (e, n, t) in nodes.items():
        if t.get("highway") == "crossing" and t.get("crossing") in ("zebra", "marked", "uncontrolled"):
            x, y = px((e, n))
            rr = 2.0 * PPM
            d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=LINE, width=1)
    # Under the buildings: the model covers it; a plain grey there keeps a lit edge from showing.
    for w, t, p in ways:
        if "building" in t and len(p) > 2 and t.get("building") not in ("roof", "carport"):
            d.polygon(poly(p), fill=UNDER)
    arr = np.asarray(im, np.float32)
    # Shade under every LiDAR crown: the ground under a Canberra street tree is darker and greener.
    sh = Image.new("L", (SIZE, SIZE), 0)
    sd = ImageDraw.Draw(sh)
    for ring in crowns:
        sd.polygon(poly(ring), fill=150)
    sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(PPM * 0.8)), np.float32)[..., None] / 255
    arr = arr * (1 - 0.42 * sh) + np.array([-4.0, 6.0, -6.0]) * sh
    arr += (rng.random((SIZE, SIZE, 1)) - 0.5) * 7
    arr *= 0.74          # lit by the match's sun the map reads lighter than Google Earth's ground
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def main():
    crowns = [r for f in act_layer("ACTGOV_Mature_Trees_2020", "crownHeight,crownID") for r in rings(f["geometry"])]
    im = paint(crowns)
    out = os.path.join(CACHE, "groundmap.png")
    im.save(out)
    im.resize((1024, 1024), Image.LANCZOS).save(os.path.join(CACHE, "groundmap_small.jpg"), quality=88)
    print(out, im.size)


if __name__ == "__main__":
    main()
