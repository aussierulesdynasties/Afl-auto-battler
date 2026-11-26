"""The Gabba's surroundings from OpenStreetMap (the Gabba to the MCG standard, stage 6, 2026-11-22).

Woolloongabba round the ground, 2 km a side at 1 m a pixel: Vulture, Stanley and Main Streets, the
Cross River Rail works to the west, Woolloongabba Place Park, the East Brisbane houses and their trees,
Kangaroo Point and the Brisbane River's bends, building footprints; and the buildings extruded, out to
the CBD's towers 2 km north-west. The drawing is tools/grounds/adelaide/surrounds.py's, with this
ground's origin, area and colours (docs/MCG_STANDARD.md, Surroundings).

    python3 tools/grounds/gabba/surrounds.py

Fetches the area, the river's and Norman Creek's multipolygons and four CBD tiles (buildings only) from the
OpenStreetMap API into /tmp. Writes assets/grounds/gabba/surrounds.webp, surrounds_near.webp, trees.bin,
buildings.bin and buildings_col.bin, as the Adelaide script does. The model's 0, 0 is build.py's OSM origin
(lat -27.4858478, lon 153.0380888; solved from OSM way 4049692 against osm/geo.json). Map data (c)
OpenStreetMap contributors, ODbL.
"""
import importlib.util
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("adl_surrounds", os.path.join(HERE, "..", "adelaide", "surrounds.py"))
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)
sys.path.insert(0, os.path.join(HERE, "..", "mcg"))
import glb_tris  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "gabba")
S.LAT0, S.LON0 = -27.4858478, 153.0380888
S.KX = 111320.0 * math.cos(math.radians(S.LAT0))
S.BBOX = (153.0268, -27.4958, 153.0494, -27.4758)
# The CBD and Kangaroo Point's towers, north-west past the map's edge: the skyline over the northern stand.
CBD = [(153.0180, -27.4760, 153.0268, -27.4680), (153.0268, -27.4758, 153.0360, -27.4680),
       (153.0180, -27.4680, 153.0268, -27.4610), (153.0268, -27.4680, 153.0360, -27.4610)]
S.BUILD_R = 2600.0
RELATIONS = [1627033, 7642164, 5325731]   # the Brisbane River (two sections) and Norman Creek
S.STADIUM_WAY = "4049692"
# Google Earth over Woolloongabba and East Brisbane in late spring: dry suburban lawns, dark mango and fig
# canopies, grey asphalt, the pale concrete round the ground, the brown-green river.
S.BASE = (118, 128, 92)
S.LAWN = (108, 134, 74)
S.PITCH = (100, 138, 68)
S.URBAN = (126, 126, 118)
S.WATER = (78, 86, 70)
S.PAVED = (172, 170, 162)
S.HOUSE_ROOFS = [(156, 74, 56), (132, 70, 58), (128, 130, 132), (176, 176, 172), (100, 102, 104)]
S.FLAT_ROOFS = [(204, 204, 200), (178, 178, 176), (152, 154, 154), (220, 218, 212)]
S.HOUSE_WALLS = [(222, 214, 196), (200, 160, 128), (230, 226, 214), (184, 132, 104)]


# East Brisbane and Woolloongabba's house blocks are yards and big trees round each house (Google Earth), not the
# pale grey OpenStreetMap's residential land would paint: a yard green, and trees through the yards.
YARD = (104, 128, 78)
_area_colour = S.area_colour


def area_colour(t):
    if t.get("landuse") == "residential":
        return YARD
    return _area_colour(t)


S.area_colour = area_colour


def stadium_ring(_ways):
    """The model's own footprint (east, north): the convex hull of every gabba.glb vertex over 1 m, grown 4 m."""
    from scipy.spatial import ConvexHull
    _j, tris = glb_tris.load(os.path.join(OUT, "gabba.glb"))
    p = np.concatenate([t.reshape(-1, 3) for _m, _mat, t in tris])
    p = p[p[:, 1] > 1.0]
    a = np.c_[p[:, 0], -p[:, 2]]
    hull = a[ConvexHull(a).vertices]
    c = hull.mean(0)
    grown = [tuple(c + (q - c) * (1.0 + 4.0 / np.hypot(*(q - c)))) for q in hull]
    return grown + [grown[0]]


def main():
    path = "/tmp/gabba_surrounds.osm"
    if not os.path.exists(path):
        S.fetch("https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % S.BBOX, path)
    extra = []
    for i, bb in enumerate(CBD):
        p = "/tmp/gabba_cbd_%d.osm" % i
        if not os.path.exists(p):
            S.fetch("https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % bb, p)
        extra.append(p)
    for r in RELATIONS:
        p = "/tmp/gabba_rel_%d.osm" % r
        if not os.path.exists(p):
            S.fetch("https://api.openstreetmap.org/api/0.6/relation/%d/full" % r, p)
        extra.append(p)
    mapped, ways = S.load(path, extra)
    st = stadium_ring(ways)
    trees = S.all_trees(mapped, ways)
    trees += S.fill_parks(S.paint(trees, ways), trees, ways, st)
    # the yards: every residential block filled as a garden is, a little thinner, never within 12 m of the ground
    yards = [({"leisure": "garden"}, p) for t, p in ways if t.get("landuse") == "residential" and len(p) > 3 and p[0] == p[-1]]
    dens = S.PARK_DENSITY
    S.PARK_DENSITY = 1.0 / 180.0
    trees += S.fill_parks(S.paint(trees, ways), trees, yards, st)
    S.PARK_DENSITY = dens
    im = S.paint(trees, ways)
    im.save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    S.paint(trees, ways, S.NEAR_SIZE, S.NEAR_SPAN).save(os.path.join(OUT, "surrounds_near.webp"), quality=88, method=6)
    S._PX["size"], S._PX["ppm"] = S.SIZE, 1.0
    t = S.tree_list(trees, st)
    t.tofile(os.path.join(OUT, "trees.bin"))
    b, bc = S.building_list(ways, st)
    b.tofile(os.path.join(OUT, "buildings.bin"))
    bc.tofile(os.path.join(OUT, "buildings_col.bin"))
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b))


if __name__ == "__main__":
    main()
