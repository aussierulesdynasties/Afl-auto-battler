"""The SCG's north stands in three tiers (SCG rebuild, 2026-11-22).

The model (#1909) seats the Messenger, Noble and Bradman stands as one long rake from the fence to the
boxes. Google Earth from the field and from above shows three tiers, each with its own front: a pale
parapet over the dark void of the concourse behind the tier below. This builds those two tier fronts
as solid geometry (GroundModels.PARTS) and takes out the seats where they stand:

- per degree of the north stands (TIERS_FROM to TIERS_TO), the seats' radius against height is fitted;
- at each break height the seats within GAP metres are removed (a gangway's worth), and any seat that
  leaves alone;
- a floor, a dark recess 1.6 m high, then a pale parapet 1.1 m high standing 0.5 m proud, and the
  tier's top deck behind it, all real faces with their normals.

    python3 tools/grounds/scg/tiers.py

Rewrites assets/grounds/scg/seats_seat_scg_teal.bin (only removes seats; running it again removes
none) and writes assets/grounds/scg/tiers.bin (triangles, per vertex x, y, z, normal, colour).
"""
import math
import os

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg")
PC = np.array([0.94, 11.82])
TIERS_FROM, TIERS_TO = 44.0, 98.0       # degrees anticlockwise from east: the Messenger, Noble, Bradman
BREAKS = (7.2, 13.4)                   # tier fronts, metres up (top seats are at 18-20 m)
GAP = 0.9
FLOOR = (0.42, 0.42, 0.41)
VOID = (0.05, 0.055, 0.06)
PARAPET = (0.80, 0.79, 0.76)
DECK = (0.55, 0.55, 0.53)


def main():
    path = os.path.join(DIR, "seats_seat_scg_teal.bin")
    s = np.fromfile(path, "<f4").reshape(-1, 12)
    x, y, z = s[:, 3], s[:, 7], s[:, 11]
    ang = np.degrees(np.arctan2(-(z - PC[1]), x - PC[0]))
    r = np.hypot(x - PC[0], z - PC[1])
    sector = (ang > TIERS_FROM - 0.5) & (ang < TIERS_TO + 0.5)
    drop = np.zeros(len(s), bool)
    for yb in BREAKS:
        drop |= sector & (np.abs(y - yb) < GAP)
    # a seat the gangway left on its own (no neighbour within 1 m) goes too: the seat rule's company
    from scipy.spatial import cKDTree
    while True:
        keep = ~drop
        pts = np.c_[x, y, z][keep]
        cnt = np.array([len(n) for n in cKDTree(pts).query_ball_point(pts, 1.0)])
        lone = np.flatnonzero(keep)[cnt < 2]
        if not len(lone):
            break
        drop[lone] = True
    s[~drop].astype("<f4").tofile(path)
    fits = {}
    for a in np.arange(TIERS_FROM, TIERS_TO + 0.01, 1.0):
        m = (np.abs(ang - a) < 1.5) & (y > 2.0)
        if m.sum() < 30:
            continue
        b, c = np.polyfit(y[m], r[m], 1)
        fits[a] = (b, c)
    tris = []

    def quad(p0, p1, p2, p3, n, col):
        for t in ((p0, p1, p2), (p0, p2, p3)):
            for p in t:
                tris.extend(list(p) + list(n) + list(col))

    def at(a, rr, yy):
        rad = math.radians(a)
        return (PC[0] + rr * math.cos(rad), yy, PC[1] - rr * math.sin(rad))

    keys = sorted(fits)
    for a0, a1 in zip(keys, keys[1:]):
        if a1 - a0 > 1.01:
            continue
        am = math.radians((a0 + a1) / 2)
        inward = (-math.cos(am), 0.0, math.sin(am))
        for yb in BREAKS:
            r0 = [fits[a][0] * yb + fits[a][1] for a in (a0, a1)]
            # floor of the walkway, from the parapet line back into the recess
            f0, f1 = yb - GAP + 0.1, yb - GAP + 0.1
            quad(at(a0, r0[0] - 0.6, f0), at(a1, r0[1] - 0.6, f1), at(a1, r0[1] + 1.4, f1), at(a0, r0[0] + 1.4, f0), (0, 1, 0), FLOOR)
            # the dark void under the tier above, at the back of the walkway
            quad(at(a0, r0[0] + 1.4, f0), at(a1, r0[1] + 1.4, f1), at(a1, r0[1] + 1.4, yb + 0.7), at(a0, r0[0] + 1.4, yb + 0.7), inward, VOID)
            # the tier front: a parapet standing proud, its top and the deck behind it
            top = yb + GAP + 0.2
            quad(at(a0, r0[0] - 0.6, yb + 0.7 - 0.6), at(a1, r0[1] - 0.6, yb + 0.7 - 0.6), at(a1, r0[1] - 0.6, top), at(a0, r0[0] - 0.6, top), inward, PARAPET)
            quad(at(a0, r0[0] - 0.6, yb + 0.1), at(a1, r0[1] - 0.6, yb + 0.1), at(a1, r0[1] + 1.4, yb + 0.7), at(a0, r0[0] + 1.4, yb + 0.7), (0, -1, 0), VOID)
            quad(at(a0, r0[0] - 0.6, top), at(a1, r0[1] - 0.6, top), at(a1, r0[1] + 0.2, top), at(a0, r0[0] + 0.2, top), (0, 1, 0), DECK)
    arr = np.array(tris, "<f4")
    arr.tofile(os.path.join(DIR, "tiers.bin"))
    print("seats removed %d (of %d); tiers.bin %d triangles over %d degrees" % (drop.sum(), len(s), len(arr) // 27, len(keys)))


if __name__ == "__main__":
    main()
