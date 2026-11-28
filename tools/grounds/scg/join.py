"""The stair tower where the north stands meet the Members' Pavilion (SCG rebuild, 2026-11-22).

The model (#1909, geo.py polar_box(105, 110, 108, 120, 19.5, 'brick')) put a windowless maroon brick box
here. Google Earth from the field shows a tall pale concrete tower: pilasters standing proud, a dark open
stair slot down its middle with the landings showing, a flat capping. This builds that tower as solid
geometry over the brick box (GroundModels.PARTS), every face modelled, nothing painted:

- the tower 0.2 m outside the old box on every side, pale concrete, a capping 0.4 m proud;
- on the field face five pilasters 0.45 m proud, and between the middle two an open stair slot 1.4 m
  deep, dark inside, a landing slab every 3.2 m and a balustrade at each.

    python3 tools/grounds/scg/join.py

It also folds the old brick box flat to the ground in the shipped glb (scg_part1/2.glb), so the stair slot
shows its own dark back and not brick; running it again folds nothing more.

Writes assets/grounds/scg/join.bin: triangles, per vertex x, y, z, normal, colour (float32, model metres).
"""
import math
import os

import numpy as np

import messenger_roof as glb

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg", "join.bin")
PC = np.array([0.94, 11.82])
A0, A1 = 104.8, 110.2            # degrees anticlockwise from east
R0, R1 = 107.8, 120.2            # field face, back face
TOP = 19.7
CONC = (0.78, 0.77, 0.73)
PIER = (0.84, 0.83, 0.79)
VOID = (0.07, 0.075, 0.08)
SLAB = (0.62, 0.61, 0.58)
CAP = (0.70, 0.69, 0.66)

tris = []


def at(a, r, y):
    rad = math.radians(a)
    return np.array([PC[0] + r * math.cos(rad), y, PC[1] - r * math.sin(rad)])


def quad(p0, p1, p2, p3, col, toward=None):
    """A quad whose normal faces `toward` (a point it should face) or, without one, the winding's own."""
    n = np.cross(p1 - p0, p3 - p0)
    n /= np.linalg.norm(n)
    if toward is not None and n @ (toward - (p0 + p2) / 2) < 0:
        p1, p3 = p3, p1
        n = -n
    for t in ((p0, p1, p2), (p0, p2, p3)):
        for p in t:
            tris.extend(list(p) + list(n) + list(col))


def box(a0, a1, r0, r1, y0, y1, col, faces="all"):
    """A polar box; faces: which of front (pitch side), back, sides, top to draw."""
    mid = at((a0 + a1) / 2, (r0 + r1) / 2, (y0 + y1) / 2)
    out = lambda p: 2 * p - mid    # a point beyond the face, away from the box's middle
    f = []
    if faces == "all" or "front" in faces:
        f.append((at(a0, r0, y0), at(a1, r0, y0), at(a1, r0, y1), at(a0, r0, y1)))
    if faces == "all" or "back" in faces:
        f.append((at(a0, r1, y0), at(a1, r1, y0), at(a1, r1, y1), at(a0, r1, y1)))
    if faces == "all" or "sides" in faces:
        f.append((at(a0, r0, y0), at(a0, r1, y0), at(a0, r1, y1), at(a0, r0, y1)))
        f.append((at(a1, r0, y0), at(a1, r1, y0), at(a1, r1, y1), at(a1, r0, y1)))
    if faces == "all" or "top" in faces:
        f.append((at(a0, r0, y1), at(a1, r0, y1), at(a1, r1, y1), at(a0, r1, y1)))
    if faces == "all" or "bottom" in faces:
        f.append((at(a0, r0, y0), at(a1, r0, y0), at(a1, r1, y0), at(a0, r1, y0)))
    for q in f:
        c = sum(q) / 4
        quad(*q, col, toward=out(c))


def fold_brick():
    """The model's brick box: every brick vertex inside its footprint brought down to the ground."""
    folded = 0
    for f in ("scg_part1.glb", "scg_part2.glb"):
        path = os.path.join(os.path.dirname(OUT), f)
        j, bin_ = glb.read(path)
        changed = False
        for pr in j["meshes"][0]["primitives"]:
            if j["materials"][pr["material"]]["name"] != "brick":
                continue
            acc = pr["attributes"]["POSITION"]
            idx = glb.view(j, bin_, acc)
            v = glb.get3_fast(bin_, idx)
            ang, r = glb.polar(v)
            m = (ang > 104.9) & (ang < 110.1) & (r > 107.9) & (r < 120.1) & (v[:, 1] > 0.01)
            if not m.any():
                continue
            v[m, 1] = 0.0
            glb.put3(bin_, idx, v)
            a = j["accessors"][acc]
            a["min"] = [float(x) for x in v.min(0)]
            a["max"] = [float(x) for x in v.max(0)]
            folded += int(m.sum())
            changed = True
        if changed:
            glb.write(path, j, bin_)
    return folded


def main():
    print("brick vertices folded: %d" % fold_brick())
    dpm = 180.0 / (math.pi * R0)            # degrees per metre along the field face
    # the slot: the middle 2.6 m of the face, from 2.4 m up to 1.2 m under the top
    sm = (A0 + A1) / 2
    s0, s1 = sm - 1.3 * dpm, sm + 1.3 * dpm
    y0s, y1s = 2.4, TOP - 1.2
    # field face round the slot
    for (a0, a1, y0, y1) in ((A0, s0, 0.0, TOP), (s1, A1, 0.0, TOP), (s0, s1, 0.0, y0s), (s0, s1, y1s, TOP)):
        box(a0, a1, R0, R0 + 0.01, y0, y1, CONC, faces="front")
    box(A0, A1, R0, R1, 0.0, TOP, CONC, faces=("back", "sides"))
    box(A0, A1, R0, R1, 0.0, TOP, CONC, faces="top")
    # the slot: dark back, dark sides, a landing every 3.2 m with a pale edge and a balustrade
    box(s0, s1, R0 + 1.4, R0 + 1.41, y0s, y1s, VOID, faces="front")
    for a in (s0, s1):
        p = [at(a, R0, y0s), at(a, R0 + 1.4, y0s), at(a, R0 + 1.4, y1s), at(a, R0, y1s)]
        quad(*p, VOID, toward=at(sm, R0 + 0.7, (y0s + y1s) / 2))
    quad(at(s0, R0, y1s), at(s1, R0, y1s), at(s1, R0 + 1.4, y1s), at(s0, R0 + 1.4, y1s), VOID, toward=at(sm, R0 + 0.7, 0.0))
    y = y0s
    while y < y1s - 0.5:
        box(s0, s1, R0 + 0.05, R0 + 1.4, y, y + 0.25, SLAB, faces=("front", "top", "bottom"))
        box(s0, s1, R0 + 0.05, R0 + 0.15, y + 0.25, y + 1.05, SLAB, faces=("front", "top"))
        y += 3.2
    # pilasters: at each corner and either side of the slot, 0.6 m wide, 0.45 m proud
    w = 0.3 * dpm
    for a in (A0 + w, s0 - w, s1 + w, A1 - w, (A0 + s0) / 2):
        box(a - w, a + w, R0 - 0.45, R0, 0.0, TOP, PIER, faces=("front", "sides", "top"))
    # the capping, proud all round
    cap = 0.4 * dpm
    box(A0 - cap, A1 + cap, R0 - 0.6, R1 + 0.4, TOP, TOP + 0.5, CAP)
    arr = np.array(tris, "<f4")
    arr.tofile(OUT)
    print("join.bin: %d triangles" % (len(arr) // 27))


if __name__ == "__main__":
    main()
