"""Slab edges on the MCG's outside walls (MCG flagship, model rebuild).

The model's walls are flat planes with the floors painted on, so from any angle but square-on they
read as boxes. From Google Earth every stand's back wall shows a projecting slab edge at each floor,
throwing a line of shade. This cuts every outside wall of the model (its fac_*, backclad,
backglass and uc_back faces) at each floor, LEVEL m apart, and lays a ledge DEPTH m deep along the
cut: top, face and underside, in the wall's concrete grey. Writes assets/grounds/mcg/ledges.bin
(per vertex x, y, z, normal, colour; float32, glTF metres) for GroundModels.PARTS.

    python3 tools/grounds/mcg/ledges.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_tris import load  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
GLB = os.path.join(ROOT, "assets", "grounds", "mcg", "mcg.glb")
OUT = os.path.join(ROOT, "assets", "grounds", "mcg", "ledges.bin")

WALLS = ("fac_", "backclad", "backglass", "uc_back")
FIRST = 4.2          # the first floor's slab, m above the plaza
LEVEL = 3.6          # floor to floor
DEPTH = 0.45         # how far a slab edge stands out
THICK = 0.32
MIN_LEN = 1.2        # shorter cuts (a triangle's tip) get no ledge
CONCRETE = (0.70, 0.70, 0.68)
GLASS_EDGE = (0.50, 0.52, 0.54)   # slab edges across a glass wall: the mullions' grey


def cut(t, h):
    """The segment where triangle t crosses the plane y = h, or None."""
    pts = []
    for i in range(3):
        a, b = t[i], t[(i + 1) % 3]
        if (a[1] - h) * (b[1] - h) < 0:
            s = (h - a[1]) / (b[1] - a[1])
            pts.append(a + (b - a) * s)
    return (pts[0], pts[1]) if len(pts) == 2 else None


def main():
    _, meshes = load(GLB)
    out = []
    for name, mat, tris in meshes:
        if not mat.startswith(WALLS):
            continue
        col = GLASS_EDGE if "glass" in mat else CONCRETE
        nr = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        ln = np.linalg.norm(nr, axis=1)
        for t, n, l in zip(tris, nr, ln):
            if l < 1e-6 or abs(n[1]) / l > 0.2:
                continue
            o = np.array([n[0], 0.0, n[2]])
            o /= np.linalg.norm(o)
            lo, hi = t[:, 1].min(), t[:, 1].max()
            k = int(np.ceil((lo + 0.6 - FIRST) / LEVEL))
            while FIRST + k * LEVEL < hi - 0.6:
                h = FIRST + k * LEVEL
                k += 1
                seg = cut(t, h)
                if seg is None or np.linalg.norm(seg[1] - seg[0]) < MIN_LEN:
                    continue
                p0, p1 = seg
                q0, q1 = p0 + o * DEPTH, p1 + o * DEPTH
                dn = np.array([0.0, -THICK, 0.0])
                up = np.array([0.0, 1.0, 0.0])
                quads = [((p0, p1, q1, q0), up), ((q0, q1, q1 + dn, q0 + dn), o), ((q0 + dn, q1 + dn, p1 + dn, p0 + dn), -up)]
                for (a, b, c, d), nn in quads:
                    # Wind each face so it fronts its normal.
                    if np.dot(np.cross(b - a, c - a), nn) < 0:
                        a, b, c, d = d, c, b, a
                    for p in (a, b, c, a, c, d):
                        out.append(list(p) + list(nn) + list(col))
    a = np.array(out, "<f4")
    a.tofile(OUT)
    print("ledge triangles", len(a) // 3)


if __name__ == "__main__":
    main()
