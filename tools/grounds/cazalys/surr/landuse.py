"""Rasterise OpenStreetMap land cover round Cazaly's into a class map for the background scene.

    python3 tools/grounds/cazalys/surr/landuse.py <osm dir> <out.npz> [half span m] [m per px]

Classes (CLASSES) come from OSM tags only; the sea comes from the elevation tiles (backdrop.py). Unmapped land stays 0 and
backdrop.py decides it from height and slope. Map data (c) OpenStreetMap contributors, ODbL."""
import glob, math, os, sys
import numpy as np
import osmium
from PIL import Image, ImageDraw

LAT0, LON0 = -16.935653, 145.749062
p = math.radians(LAT0)
MLAT = 111132.92 - 559.82 * math.cos(2 * p) + 1.175 * math.cos(4 * p)
MLON = 111412.84 * math.cos(p) - 93.5 * math.cos(3 * p)
CLASSES = ["unmapped", "sea", "water", "mangrove", "forest", "scrub", "farm", "grass", "suburb", "industry", "airport", "sand"]
K = {n: i for i, n in enumerate(CLASSES)}
# drawing order: later wins
ORDER = ["farm", "scrub", "forest", "grass", "suburb", "industry", "airport", "mangrove", "sand", "water"]


def cls(t):
    g = lambda k: t.get(k, "")
    if g("natural") == "water" or g("waterway") == "riverbank" or g("landuse") in ("reservoir", "basin"):
        return "water"
    if g("natural") == "wetland":
        return "mangrove" if g("wetland") in ("mangrove", "tidalflat", "saltmarsh", "") else "scrub"
    if g("natural") in ("beach", "sand") :
        return "sand"
    if g("landuse") == "forest" or g("natural") == "wood":
        return "forest"
    if g("natural") in ("scrub", "heath", "grassland"):
        return "scrub"
    if g("landuse") in ("farmland", "orchard", "plant_nursery", "farmyard", "meadow"):
        return "farm"
    if g("aeroway") == "aerodrome":
        return "airport"
    if g("leisure") in ("park", "golf_course", "pitch", "recreation_ground", "sports_centre") or g("landuse") in ("grass", "recreation_ground", "cemetery", "village_green"):
        return "grass"
    if g("landuse") in ("residential",):
        return "suburb"
    if g("landuse") in ("industrial", "commercial", "retail", "railway", "construction", "port", "quarry", "landfill"):
        return "industry"
    return None


class H(osmium.SimpleHandler):
    """closed tagged ways and multipolygon relations (outer members joined end to end)"""
    def __init__(s):
        super().__init__(); s.polys = {n: [] for n in CLASSES}; s.ways = {}; s.rels = []; s.seen = set()

    def way(s, w):
        try:
            pts = [(n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        s.ways[w.id] = pts
        c = cls({t.k: t.v for t in w.tags})
        if c and len(pts) > 3 and w.nodes[0].ref == w.nodes[-1].ref and w.id not in s.seen:
            s.seen.add(w.id); s.polys[c].append(pts)

    def relation(s, r):
        t = {x.k: x.v for x in r.tags}
        if t.get("type") != "multipolygon":
            return
        c = cls(t)
        if c and r.id not in s.seen:
            s.seen.add(r.id); s.rels.append((c, [m.ref for m in r.members if m.type == "w" and m.role in ("outer", "")]))

    def finish(s):
        for c, refs in s.rels:
            segs = [list(s.ways[i]) for i in refs if i in s.ways]
            while segs:
                ring = segs.pop(0)
                grown = True
                while grown and ring[0] != ring[-1]:
                    grown = False
                    for k, g in enumerate(segs):
                        if g[0] == ring[-1]: ring += g[1:]
                        elif g[-1] == ring[-1]: ring += g[::-1][1:]
                        elif g[-1] == ring[0]: ring = g[:-1] + ring
                        elif g[0] == ring[0]: ring = g[::-1][:-1] + ring
                        else: continue
                        segs.pop(k); grown = True; break
                if len(ring) > 3:
                    s.polys[c].append(ring)


def main():
    d, out = sys.argv[1], sys.argv[2]
    half = float(sys.argv[3]) if len(sys.argv) > 3 else 21000.0
    res = float(sys.argv[4]) if len(sys.argv) > 4 else 20.0
    n = int(2 * half / res)
    h = H()
    for f in sorted(glob.glob(os.path.join(d, "*.osm"))):
        h.apply_file(f, locations=True)
    h.finish()
    px = lambda lon, lat: ((lon - LON0) * MLON / res + n / 2, n / 2 - (lat - LAT0) * MLAT / res)
    im = Image.new("L", (n, n), 0); dr = ImageDraw.Draw(im)
    for c in ORDER:
        for ring in h.polys[c]:
            if len(ring) > 2:
                dr.polygon([px(*q) for q in ring], fill=K[c])
    a = np.asarray(im).copy()
    np.savez_compressed(out, cls=a, res=res, half=half, names=np.array(CLASSES))
    u, c = np.unique(a, return_counts=True)
    print({CLASSES[i]: round(k / a.size, 3) for i, k in zip(u, c)})


if __name__ == "__main__":
    main()
