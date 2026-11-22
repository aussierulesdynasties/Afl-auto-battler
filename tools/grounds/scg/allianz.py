"""Allianz Stadium beside the SCG, as a plain massing for the SCG's surroundings (SCG rebuild, 2026-11-22).

Allianz Stadium stands 150 m north-west of the SCG and fills the view past the Messenger, Noble and
Bradman stands from much of the ground. Its OpenStreetMap outline (way 685551995) and pitch (way
1089645022) give the plan; Google Earth gives the look: a white roof ring that covers every seat over
a rectangular opening, on a dark silver outer wall, a steep bowl of dark blue seats inside. It is a
neighbour seen from 150 m and more, never the match's ground, so it keeps to what reads from there, all of
it modelled: the wall's vertical fins and floor edges standing proud, the dark glazed concourse set back
under them, and the roof's radial ribs.

    python3 tools/grounds/scg/allianz.py [tile.osm ...]     (the tiles tools/grounds/scg/surrounds.py fetched)

Writes assets/grounds/scg/allianz.glb in the SCG model's metres (x east, y up, z south).
Map data (c) OpenStreetMap contributors, ODbL.
"""
import glob
import math
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg", "allianz.glb")
LAT0, LON0 = -33.8916, 151.2248
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110574.0
STADIUM, PITCH = "685551995", "1089645022"
N = 160

WALL_TOP, ROOF_OUT, ROOF_IN = 27.0, 33.0, 38.5      # metres: outer wall, roof at the outer and inner edge
COL = {"wall": (74, 78, 84), "roof": (236, 236, 232), "under": (120, 124, 126),
       "seats": (58, 72, 92), "pitch": (92, 136, 60), "plinth": (150, 150, 146),
       "fin": (134, 138, 140), "glass": (40, 46, 54), "rib": (214, 214, 210),
       "clear": (176, 182, 184), "riser": (34, 40, 52), "aisle": (150, 150, 146), "slab": (150, 150, 146), "fascia": (210, 210, 206)}
BASE = 5.0                      # the glazed concourse at the foot of the wall, set back BASE_IN metres
BASE_IN = 2.5
FLOORS = (10.0, 16.0, 22.0)     # floor edges on the outer wall


def load(files):
    nodes, ways = {}, {}
    for f in files:
        r = ET.parse(f).getroot()
        for n in r.findall("node"):
            nodes[n.get("id")] = ((float(n.get("lon")) - LON0) * KX, (float(n.get("lat")) - LAT0) * KY)
        for w in r.findall("way"):
            ways[w.get("id")] = [nd.get("ref") for nd in w.findall("nd")]
    return [np.array([nodes[i] for i in ways[k] if i in nodes]) for k in (STADIUM, PITCH)]


def radial(poly, c):
    """The polygon as a radius for each of N angles round c."""
    p = poly - c
    out = np.zeros(N)
    for k in range(N):
        a = 2 * math.pi * k / N
        d = np.array([math.cos(a), math.sin(a)])
        best = 0.0
        for i in range(len(p) - 1):
            A, B = p[i], p[i + 1]
            M = np.array([d, A - B]).T
            if abs(np.linalg.det(M)) < 1e-9:
                continue
            t, s = np.linalg.solve(M, A)
            if t > 0 and 0 <= s <= 1:
                best = max(best, t)
        out[k] = best
    return out


def ring(c, r, y):
    a = 2 * np.pi * np.arange(N) / N
    e, n = c[0] + r * np.cos(a), c[1] + r * np.sin(a)
    return np.c_[e, np.full(N, y), -n]


def strip(r0, r1, flip=False):
    v = np.r_[r0, r1]
    f = []
    for k in range(N):
        a, b, c_, d = k, (k + 1) % N, N + (k + 1) % N, N + k
        f += [[a, b, c_], [a, c_, d]] if not flip else [[a, c_, b], [a, d, c_]]
    return v, np.array(f)


def disc(c, r, y, up=True):
    v = np.r_[ring(c, r, y), [[c[0], y, -c[1]]]]
    f = [[N, (k + 1) % N, k] if up else [N, k, (k + 1) % N] for k in range(N)]
    return v, np.array(f)


def part(meshes, name, vf, face="up", c=None):
    """One part in one colour, its faces turned to face `face`: up, down or out (from c)."""
    m = trimesh.Trimesh(vertices=vf[0], faces=vf[1], process=False)
    n, ctr = m.face_normals, m.triangles_center
    want = {"up": n[:, 1], "down": -n[:, 1]}.get(face)
    if want is None:
        want = n[:, 0] * (ctr[:, 0] - c[0]) + n[:, 2] * (ctr[:, 2] + c[1])
    if np.mean(want) < 0:
        m.faces = m.faces[:, ::-1]
    col = [(c / 255.0) ** 2.2 for c in COL[name]] + [1.0]     # glTF colours are linear; COL is sRGB
    m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        name="allianz_" + name, baseColorFactor=col, metallicFactor=0.0, roughnessFactor=0.9, doubleSided=True))
    meshes.append((name, m))


def steps(meshes, c, r0, y0, r1, y1, row=0.85, aisle_every=6, aisle_w=1.3):
    """A rake of seat rows from (r0, y0) to (r1, y1): for every row a riser and a tread of seats, so the
    tier reads stepped, as it is, and not as a ramp; every `aisle_every` bays an aisle 1.3 m wide whose
    treads are bare concrete steps."""
    rows = max(2, int(round(float(np.mean(r1 - r0)) / row)))
    out = {"seats": [], "aisle": [], "riser": []}

    def P(a, r, y):
        return [c[0] + r * math.cos(a), y, -(c[1] + r * math.sin(a))]

    def rad(arr, a):
        return float(np.interp(a % (2 * np.pi), np.r_[2 * np.pi * np.arange(N) / N, 2 * np.pi], np.r_[arr, arr[0]]))

    for k in range(N):
        a0, a1 = 2 * np.pi * k / N, 2 * np.pi * (k + 1) / N
        spans = [(a0, a1, "seats")]
        if k % aisle_every == 0:
            mid, half = (a0 + a1) / 2, aisle_w / 2 / rad(r0, (a0 + a1) / 2)
            spans = [(a0, mid - half, "seats"), (mid - half, mid + half, "aisle"), (mid + half, a1, "seats")]
        for sa, sb, kind in spans:
            ra0, ra1, rb0, rb1 = rad(r0, sa), rad(r1, sa), rad(r0, sb), rad(r1, sb)
            for j in range(rows):
                f0, f1 = j / rows, (j + 1) / rows
                ya, yb = y0 + (y1 - y0) * f0, y0 + (y1 - y0) * f1
                qa0, qa1 = ra0 + (ra1 - ra0) * f0, ra0 + (ra1 - ra0) * f1
                qb0, qb1 = rb0 + (rb1 - rb0) * f0, rb0 + (rb1 - rb0) * f1
                out["riser"].append([P(sa, qa0, ya), P(sb, qb0, ya), P(sb, qb0, yb), P(sa, qa0, yb)])
                out[kind].append([P(sa, qa0, yb), P(sb, qb0, yb), P(sb, qb1, yb), P(sa, qa1, yb)])
    for name, quads in out.items():
        q = np.array(quads, float)
        v = q.reshape(-1, 3)
        i = np.arange(len(q)) * 4
        f = np.r_[np.c_[i, i + 1, i + 2], np.c_[i, i + 2, i + 3]]
        part(meshes, name, (v, f), "up" if name != "riser" else "out", c)
        if name == "riser":
            meshes[-1][1].faces = meshes[-1][1].faces[:, ::-1]        # risers face the pitch


def solid(meshes, name, boxes):
    """Closed boxes (each 8 corners) as one part: convex hulls, so every face points out."""
    ms = [trimesh.convex.convex_hull(np.array(b)) for b in boxes]
    m = trimesh.util.concatenate(ms)
    col = [(c / 255.0) ** 2.2 for c in COL[name]] + [1.0]     # glTF colours are linear; COL is sRGB
    m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        name="allianz_" + name, baseColorFactor=col, metallicFactor=0.0, roughnessFactor=0.8, doubleSided=False))
    meshes.append((name, m))


def at(c, r, a, y):
    return [c[0] + r * math.cos(a), y, -(c[1] + r * math.sin(a))]


def main():
    files = sys.argv[1:] or sorted(glob.glob("/tmp/scg_surrounds_*.osm"))
    outline, pitch = load(files)
    c = pitch[:-1].mean(0)
    # The stadium outline takes in the forecourt; the building ends about 60 m past the pitch (Google Earth).
    ro = np.minimum(radial(outline, c) - 2.0, radial(pitch, c) + 60.0)
    rp = radial(pitch, c)
    rf = rp + 5.0                      # the front row, 5 m off the pitch
    rin = rp + 9.0                     # the roof's inner edge, a little past the front row
    rtop = rf + (ro - rf) * 0.78       # the back row
    meshes = []
    part(meshes, "wall", strip(ring(c, ro, BASE), ring(c, ro, WALL_TOP)), "out", c)
    # the concourse: dark glass set back under the wall, and the wall's underside over it
    part(meshes, "glass", strip(ring(c, ro - BASE_IN, 0.0), ring(c, ro - BASE_IN, BASE)), "out", c)
    part(meshes, "under", strip(ring(c, ro - BASE_IN, BASE), ring(c, ro, BASE)), "down")
    ang = 2 * np.pi * np.arange(N) / N
    fins, floors, ribs, ribs_under, girder = [], [], [], [], []
    for k in range(N):
        for f in (0.0, 0.5):
            a = ang[k] + f * 2 * np.pi / N
            r = float(np.interp(a, np.r_[ang, 2 * np.pi], np.r_[ro, ro[0]]))
            w = 0.18 / r
            fins.append([at(c, rr, a + s_, y) for rr in (r - 0.05, r + 0.6) for s_ in (-w, w) for y in (BASE - 0.4, WALL_TOP)])
            # a column down through the concourse every other fin
            if f == 0.0 and k % 2 == 0:
                w2 = 0.3 / r
                fins.append([at(c, rr, a + s_, y) for rr in (r - BASE_IN - 0.3, r - BASE_IN + 0.3) for s_ in (-w2, w2) for y in (0.0, BASE)])
        k1 = (k + 1) % N
        for yf in FLOORS:
            floors.append([at(c, rr, a_, y) for a_, r_ in ((ang[k], ro[k]), (ang[k] + 2 * np.pi / N, ro[k1]))
                           for rr in (r_ - 0.05, r_ + 0.75) for y in (yf, yf + 0.35)])
        if k % 3 == 0:
            # a radial rib along the roof's top from the outer edge to the inner
            w = 0.25 / ro[k]
            ribs.append([at(c, r_, ang[k] + s_, y) for r_, y0 in ((ro[k], ROOF_OUT), (rin[k], ROOF_IN))
                         for s_ in (-w, w) for y in (y0 - 0.05, y0 + 0.35)])
        # a rib under the roof every third step, from the outer wall to the leading edge
        if k % 3 == 0:
            w = 0.35 / ro[k]
            ribs_under.append([at(c, r_, ang[k] + s_, y) for r_, y0 in ((ro[k], WALL_TOP), (rin[k], ROOF_IN - 1.2))
                               for s_ in (-w, w) for y in (y0 - 1.6, y0 - 0.05)])
    # the leading edge: a box girder all round
    for k in range(N):
        k1 = (k + 1) % N
        girder.append([at(c, r_ + d, a_, y) for a_, r_ in ((ang[k], rin[k]), (ang[k] + 2 * np.pi / N, rin[k1]))
                       for d in (-0.2, 1.4) for y in (ROOF_IN - 2.6, ROOF_IN + 0.1)])
    solid(meshes, "rib", ribs_under + girder)
    solid(meshes, "fin", fins + floors)
    solid(meshes, "rib", ribs)
    part(meshes, "plinth", strip(ring(c, rtop, 24.0), ring(c, ro, 24.0)))
    # two tiers with the boxes between them: a lower rake to 11 m, a dark glazed band set back 1.5 m with
    # a pale fascia over it, then the upper rake from 14.5 m to the back row
    rmid = rf + (rtop - rf) * 0.45
    steps(meshes, c, rf, 1.5, rmid, 11.0)
    part(meshes, "slab", strip(ring(c, rmid, 11.0), ring(c, rmid + 1.5, 11.0)))
    part(meshes, "glass", strip(ring(c, rmid + 1.5, 11.0), ring(c, rmid + 1.5, 13.6)), "out", c)
    part(meshes, "glass", strip(ring(c, rmid + 1.5, 11.0), ring(c, rmid + 1.5, 13.6)))
    part(meshes, "fascia", strip(ring(c, rmid, 13.6), ring(c, rmid, 14.6)), "out", c)
    part(meshes, "fascia", strip(ring(c, rmid, 13.6), ring(c, rmid + 1.5, 13.6)), "down")
    part(meshes, "fascia", strip(ring(c, rmid, 14.6), ring(c, rmid + 1.5, 14.6)))
    # the fascia faces the pitch: turn it in, not out
    meshes[-3][1].faces = meshes[-3][1].faces[:, ::-1]
    steps(meshes, c, rmid + 1.5, 14.6, rtop, 24.0)
    # the roof: white sheeting from the outer edge, a translucent band over the front rows, the leading
    # edge's box girder
    rband = rin + (ro - rin) * 0.28
    yband = ROOF_IN + (ROOF_OUT - ROOF_IN) * 0.28
    part(meshes, "roof", strip(ring(c, ro, ROOF_OUT), ring(c, rband, yband)))
    part(meshes, "clear", strip(ring(c, rband, yband), ring(c, rin, ROOF_IN)))
    part(meshes, "roof", strip(ring(c, ro, WALL_TOP), ring(c, ro, ROOF_OUT)), "out", c)
    part(meshes, "under", strip(ring(c, rin, ROOF_IN - 1.2), ring(c, ro, WALL_TOP)), "down")
    part(meshes, "under", strip(ring(c, rin, ROOF_IN - 1.2), ring(c, rin, ROOF_IN)), "out", c)
    part(meshes, "pitch", disc(c, rf, 0.6))     # clear of the map under it, or they flicker at 200 m
    scene = trimesh.Scene()
    for i, (name, m) in enumerate(meshes):
        scene.add_geometry(m, node_name="allianz_%s_%d" % (name, i), geom_name="allianz_%s_%d" % (name, i))
    scene.export(OUT, include_normals=True)
    print("allianz.glb", OUT, "outer radius %.0f-%.0f m" % (ro.min(), ro.max()))


if __name__ == "__main__":
    main()
