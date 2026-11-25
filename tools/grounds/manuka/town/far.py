"""Manuka's distant Canberra, past the town (town.py, the first 1.08 km) out to 30 km: Red Hill and Mount Mugga
Mugga to the south, Capital Hill and Parliament House with its flag mast to the north-west, Lake Burley Griffin, Mount
Ainslie and Mount Majura north, Black Mountain with the Telstra (Black Mountain) Tower, and the Brindabellas on the
western skyline.

    python3 tools/grounds/manuka/town/far.py      # writes assets/grounds/manuka/manuka_backdrop_part2.glb

The buildings, roads and trees between the town and 6.5 km are mid.py's (part3), standing on this land.

Heights: Terrarium tiles (zoom 13, about 16 m a sample here). The land is coloured by height and slope (the suburbs'
grey-green, dry grass, the reserves' bush), the lake by its level; nothing is aerial imagery. Parliament House is its
OpenStreetMap outline (way 5035605) stood up to its roof line, with the four-legged flag mast (node 163535624: 50 m
to 101 m above the hill); the tower is modelled from its published form (195.2 m: podium, shaft, the stacked
observation decks and the mast).
"""
import math
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASSETS, C, CACHE, Dem, _get, en  # noqa: E402
import town as T  # noqa: E402

R_IN, R_OUT = 1060.0, 30000.0
BLEND = (1060.0, 1600.0)
EARTH_R = 6371000.0
LAKE = 556.0 - 574.4          # Lake Burley Griffin's level, m from the field
SUBURB = np.array([92, 102, 78], float)      # Canberra's leafy suburbs from afar: more tree than roof
GRASS = np.array([166, 148, 104], float)
BUSH = np.array([64, 78, 54], float)
PINE = np.array([50, 66, 46], float)
WATER = np.array([74, 104, 118], float)


def noise(shape, cells, seed):
    from PIL import Image
    g = np.random.default_rng(seed).random(cells).astype(np.float32)
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((shape[1], shape[0]), Image.BICUBIC), np.float32) / 255


def land(acc_mesh):
    dem = Dem(13, R_OUT + 500)
    nb = 540
    rings = [R_IN]
    while rings[-1] < R_OUT:
        rings.append(min(R_OUT, rings[-1] * 1.024 + 6.0))
    rr = np.array(rings)
    bb = np.radians(np.arange(nb) * 360.0 / nb)
    B, Rg = np.meshgrid(bb, rr)
    E, N = C[0] + Rg * np.sin(B), C[1] + Rg * np.cos(B)
    h = dem.at(E, N)
    dy_r = np.gradient(h, axis=0) / np.gradient(Rg, axis=0)
    dy_b = np.gradient(h, axis=1) / (Rg * (2 * math.pi / nb))
    slope = np.hypot(dy_r, dy_b)
    lake = (h < LAKE + 0.9) & (slope < 0.02) & (Rg > 1200) & (Rg < 9000)
    from scipy import ndimage
    lake = ndimage.binary_opening(lake, iterations=1)
    n1 = noise(h.shape, (40, 180), 3)
    n2 = noise(h.shape, (160, 720), 4)
    bush = np.clip((slope - 0.07) * 6 + (h - 60) / 160 + (n1 - 0.5) * 1.0, 0, 1)
    sub = np.clip((50 - h) / 40 + (9000 - Rg) / 7000 + (n1 - 0.5) * 0.5, 0, 1) * (1 - bush)
    col = GRASS * (1 - bush[..., None]) + BUSH * bush[..., None]
    col = col * (1 - sub[..., None]) + SUBURB * sub[..., None]
    col *= (0.88 + 0.22 * n2)[..., None]
    col = np.where(lake[..., None], WATER * (0.95 + 0.08 * n2[..., None]), col)
    y = np.where(lake, LAKE, h)
    t = np.clip((Rg - BLEND[0]) / (BLEND[1] - BLEND[0]), 0, 1)
    t = t * t * (3 - 2 * t)
    # Inside the blend the land meets the town's edge: the town's own height there (Land.z at its edge) is the
    # same smoothed Terrarium surface, so only the curve of the earth is blended in.
    tdem = Dem(15, 1700)
    tdem.smooth(3.0)
    near = tdem.at(E, N)
    y = near * (1 - t) + y * t
    y -= Rg ** 2 / (2 * EARTH_R)
    V = np.stack([E, N, y - 0.15], -1).reshape(-1, 3)
    Cc = np.clip(col, 0, 255).reshape(-1, 3)
    F = []
    for i in range(len(rings) - 1):
        for j in range(nb):
            a, b = i * nb + j, i * nb + (j + 1) % nb
            c, d = a + nb, b + nb
            F += [(a, b, c), (b, d, c)]
    acc_mesh["v"], acc_mesh["c"], acc_mesh["f"] = V, Cc, np.array(F)
    return dem


def parliament(acc, dem):
    """Parliament House: the OSM outline to its parapet, the grassed roof walk over the middle and the mast."""
    p = _get("https://api.openstreetmap.org/api/0.6/map?bbox=149.1205,-35.3115,149.1285,-35.3050",
             os.path.join(CACHE, "parl.osm"))
    r = ET.parse(p).getroot()
    nodes = {n.get("id"): en(float(n.get("lat")), float(n.get("lon"))) for n in r.iter("node")}
    ring = None
    for w in r.iter("way"):
        if w.get("id") == "5035605":
            ring = [nodes[n.get("ref")] for n in w.iter("nd")][:-1]
    ring = T.ccw_ring(T.simplify(ring, 0.6))
    P = np.asarray(ring)
    zg = dem.at(P[:, 0], P[:, 1])
    base = float(zg.min()) - 1.0
    top = float(zg.max()) + 18.0
    key = ((99, 99), "wall")
    marble = (226, 222, 210)
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L / 4.0)
        wins = [((k + 0.3) * L / n, (k + 0.7) * L / n, top - 13.5, top - 3.0) for k in range(n)] if n >= 1 else []
        T.wall(acc, key, a, b, base, top, marble, wins, None)
    T.flat_roof(acc, ((99, 99), "roof"), ring, top, (150, 156, 140), marble, False, 0)
    # The roof walk: Capital Hill's grass carried over the building as a low mound.
    mx, my = P.mean(0)
    from shapely.geometry import Polygon
    pg = Polygon(ring).buffer(-28.0)
    if pg.geom_type == "Polygon" and not pg.is_empty:
        inner = T.ccw_ring([tuple(q) for q in list(pg.exterior.coords)[:-1]])
        acc.poly(((99, 99), "roof"), [(x, y, top + 0.9) for x, y in inner], (118, 136, 84))
    # The flag mast: four stainless legs leaning in from the roof (50 m above the hill) to 101 m, the flag on top.
    fp = en(-35.3081856, 149.1244380)
    z0 = float(dem.at(*fp))
    leg_b, leg_t = 32.0, 1.2
    steel = (214, 218, 222)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        b0 = (fp[0] + leg_b * math.cos(a), fp[1] + leg_b * math.sin(a), z0 + 50.0)
        b1 = (fp[0] + leg_t * math.cos(a), fp[1] + leg_t * math.sin(a), z0 + 101.0)
        side = np.array([-math.sin(a), math.cos(a)]) * 0.6
        acc.quad(key, (b0[0] - side[0], b0[1] - side[1], b0[2]), (b0[0] + side[0], b0[1] + side[1], b0[2]),
                 (b1[0] + side[0] * 0.4, b1[1] + side[1] * 0.4, b1[2]), (b1[0] - side[0] * 0.4, b1[1] - side[1] * 0.4, b1[2]), steel)
    fx, fy, fz = fp[0], fp[1], z0 + 101.0
    acc.quad(key, (fx, fy, fz - 6.4), (fx + 12.8, fy, fz - 6.4), (fx + 12.8, fy, fz), (fx, fy, fz), (24, 36, 110))


def tower(acc, dem):
    """The Black Mountain (Telstra) Tower, 195.2 m, on Black Mountain's summit."""
    c = en(-35.27552816, 149.09776749)
    z0 = float(dem.at(*c)) - 2.0
    key = ((98, 98), "wall")
    conc = (206, 204, 198)
    def drum(r0, r1, za, zb, col, n=16):
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            p = lambda a, r, z: (c[0] + r * math.cos(a), c[1] + r * math.sin(a), z)
            acc.quad(key, p(a0, r0, za), p(a1, r0, za), p(a1, r1, zb), p(a0, r1, zb), T.shade(col, 0.88 + 0.12 * math.cos(a0 - 2.4)))
            acc.tri(key, p(a0, r1, zb), p(a1, r1, zb), (c[0], c[1], zb), col)
            acc.tri(key, p(a1, r0, za), p(a0, r0, za), (c[0], c[1], za), T.shade(col, 0.7))
    drum(26, 26, z0, z0 + 6, conc)          # the podium
    drum(20, 18, z0 + 6, z0 + 14, conc)
    drum(8.0, 6.5, z0 + 14, z0 + 128, conc)  # the shaft
    for za, zb, r, col in ((z0 + 52, z0 + 55, 22, conc), (z0 + 58, z0 + 62, 19, (70, 78, 86)), (z0 + 62, z0 + 65, 21, conc),
                           (z0 + 68, z0 + 72, 19, (70, 78, 86)), (z0 + 72, z0 + 75, 21, conc), (z0 + 78, z0 + 84, 18, (64, 72, 80)),
                           (z0 + 84, z0 + 88, 20, conc), (z0 + 92, z0 + 96, 16, conc)):
        drum(r, r, za, zb, col)
    drum(3.2, 2.2, z0 + 128, z0 + 160, (220, 220, 216), 8)
    drum(1.4, 0.4, z0 + 160, z0 + 195.2, (196, 60, 52), 8)    # the mast, banded red and white
    for zz in (z0 + 166, z0 + 178, z0 + 189):
        drum(1.2, 1.0, zz, zz + 4, (236, 236, 232), 8)


def main():
    mesh = {}
    dem = land(mesh)
    acc = T.Acc()
    parliament(acc, dem)
    tower(acc, dem)
    import trimesh
    V = np.c_[mesh["v"][:, 0], mesh["v"][:, 2], -mesh["v"][:, 1]]
    m = trimesh.Trimesh(V, mesh["f"], process=False)
    m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.c_[mesh["c"], np.full(len(V), 255)].astype(np.uint8))
    m.visual.material = trimesh.visual.material.PBRMaterial(name="far_land", baseColorFactor=[255, 255, 255, 255],
                                                            roughnessFactor=1.0, metallicFactor=0.0)
    m.vertex_normals
    out = os.path.join(ASSETS, "manuka_backdrop_part2.glb")
    T.export(acc, None, out, extra=[("far_land", m)])
    print("far", out, "%.1f MB" % (os.path.getsize(out) / 1e6), "land verts", len(V))


if __name__ == "__main__":
    main()
