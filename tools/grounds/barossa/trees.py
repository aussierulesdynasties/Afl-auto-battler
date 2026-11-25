"""Gum trees for the land round Barossa Park: four eucalypts (the river red gums and blue gums of the paddocks, creek
lines and streets round Lyndoch), each a trunk that forks into leaning limbs, with an open crown of separate leaf
clumps so the sky shows through it, the way a gum reads from across a paddock.

Each tree is built at unit size (1 m tall, crown radius 1 m); the game scales it by the tree's own height and crown
radius from trees.bin. Writes assets/grounds/barossa/barossa_gums.glb with nodes gum<k>_leaf, gum<k>_wood and gum<k>_far (both materials).

    python3 tools/grounds/barossa/trees.py
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import Mesh, write_glb, _n  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "grounds", "barossa")

# A clump: an icosahedron (20 faces), pushed in and out a little so no two clumps share an outline, with
# its normals pointing from the clump's middle (soft, leafy shading rather than facets).
_OCT_V = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
_OCT_F = [(0, 2, 4), (4, 2, 1), (1, 2, 5), (5, 2, 0), (4, 3, 0), (1, 3, 4), (5, 3, 1), (0, 3, 5)]


def _ico():
    t = (1 + 5 ** 0.5) / 2
    v = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
         (8, 6, 7), (9, 8, 1)]
    return [_n(x) for x in v], f


ICO = _ico()
OCT = ([np.array(v, float) for v in _OCT_V], _OCT_F)


def clump(m, rng, c, rx, ry, rz, shape=None):
    verts, faces = shape or ICO
    c = np.asarray(c, float)
    bump = [1.0 + rng.uniform(-0.3, 0.3) for _ in verts]
    pts = [c + np.array((v[0] * rx, v[1] * ry, v[2] * rz)) * bump[i] for i, v in enumerate(verts)]
    p = m._p("leaf")
    for f in faces:
        for i in f:
            v = verts[i]
            p["v"].append(pts[i])
            # bent well up: leaves let sunlight through, so a gum never goes black on its shaded side
            p["n"].append(_n(_n((v[0] / rx, v[1] / ry, v[2] / rz)) + np.array((0, 0.6, 0))))
            p["uv"].append((0.0, 0.0))
            # inner and under leaves darker, the sunlit top lighter
            k = 0.55 + 0.75 * (0.5 + 0.5 * v[1])
            p["c"].append((k, k, k))


def gum(seed):
    """one eucalypt, unit height and crown radius: (near mesh, far mesh). The far one keeps the crown's outline in
    one coarse clump a limb and a three-sided trunk, for trees seen from over 450 m."""
    rng = np.random.default_rng(seed)
    m = Mesh()
    far = Mesh()
    frng = np.random.default_rng(seed + 50)
    # the skeleton is drawn Y times taller than wide, near a real gum's shape (height about 2.6 crown radii), so the
    # game's scaling by height and crown radius leaves the leaf clumps round rather than stretched
    Y = 2.6
    fork = rng.uniform(0.28, 0.42)
    lean = rng.uniform(-0.06, 0.06, 2)
    top = np.array((lean[0], fork * Y, lean[1]))
    # trunk: a little wider at the foot; bark tubes are scaled by the crown radius so stay thin here
    m.tube("wood", (0, -0.02, 0), top, 0.05, 0.036, seg=5, caps=False)
    limbs = int(rng.integers(3, 5))
    a0 = rng.uniform(0, 2 * math.pi)
    for k in range(limbs):
        a = a0 + 2 * math.pi * k / limbs + rng.uniform(-0.4, 0.4)
        out = rng.uniform(0.35, 0.75)
        rise = rng.uniform(0.32, 0.5) * (1.0 - fork) / 0.66
        end = top + np.array((math.cos(a) * out, rise * Y, math.sin(a) * out))
        bend = top + (end - top) * 0.5 + np.array((0, 0.05 * Y, 0))
        m.tube("wood", top, bend, 0.03, 0.022, seg=4, caps=False)
        m.tube("wood", bend, end, 0.022, 0.012, seg=4, caps=False)
        mid = top + (end - top) * 0.82
        clump(far, frng, mid + np.array((0, 0.03, 0)), 0.42, 0.28, 0.42, OCT)
        # the leaves hang in three to five clumps along, round and below the end of the limb, overlapping so the
        # crown reads as one open, uneven mass with sky through its gaps
        for j in range(int(rng.integers(4, 7))):
            f = 1.0 if j == 0 else rng.uniform(0.5, 1.05)
            at = top + (end - top) * f + np.array((rng.uniform(-0.2, 0.2), rng.uniform(-0.25, 0.15) * Y / 2.6,
                                                   rng.uniform(-0.2, 0.2)))
            s = rng.uniform(0.32, 0.44) * (1.0 if j == 0 else 0.85)
            clump(m, rng, at, s * rng.uniform(1.0, 1.3), s * rng.uniform(0.6, 0.85), s * rng.uniform(1.0, 1.3))
    # a leader through the middle with the crown's top clump
    tip = top + np.array((rng.uniform(-0.1, 0.1), (1.0 - fork - 0.18) * Y, rng.uniform(-0.1, 0.1)))
    m.tube("wood", top, tip, 0.026, 0.012, seg=4, caps=False)
    clump(m, rng, tip, 0.4, 0.28, 0.4)
    clump(m, rng, tip + np.array((rng.uniform(-0.2, 0.2), -0.25, rng.uniform(-0.2, 0.2))), 0.38, 0.26, 0.38)
    clump(far, frng, tip, 0.36, 0.22, 0.36, OCT)
    far.tube("wood", (0, -0.02, 0), top, 0.05, 0.036, seg=3, caps=False)
    # fit: crown reaches 1 m from the trunk and 1 m up
    allv = np.array(m.parts["leaf"]["v"])
    rad = np.max(np.hypot(allv[:, 0], allv[:, 2]))
    hi = np.max(allv[:, 1])
    for mesh in (m, far):
        for p in mesh.parts.values():
            for i, v in enumerate(p["v"]):
                p["v"][i] = np.array((v[0] / rad, v[1] / hi, v[2] / rad))
            # normals stay as they are: the non-uniform fit is mild
    return m, far


def main():
    nodes = []
    for k in range(4):
        g, far = gum(100 + k)
        leaf, wood = Mesh(), Mesh()
        leaf.parts["leaf"] = g.parts["leaf"]
        wood.parts["wood"] = g.parts["wood"]
        nodes += [("gum%d_leaf" % k, leaf), ("gum%d_wood" % k, wood), ("gum%d_far" % k, far)]
        print("gum%d" % k, leaf.tris(), "leaf tris", wood.tris(), "wood tris", far.tris(), "far tris")
    # gum leaves: a dull olive grey-green (sRGB about 76, 86, 63), lit lighter on top by the clumps' vertex shade
    mats = {"leaf": {"col": (0.072, 0.092, 0.050), "vcol": True, "rough": 1.0},
            "wood": {"col": (0.33, 0.29, 0.24), "rough": 1.0}}
    write_glb(os.path.join(OUT, "barossa_gums.glb"), nodes, mats)


if __name__ == "__main__":
    main()
