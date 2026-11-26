"""The real land under Norwood's buildings outside the ground (tools/grounds/terrain: Geoscience Australia's
5 m LiDAR bare-earth DEM, metres above the turf at the centre circle, x east / y north as here).

    with on_land(part):      # everything the block adds to `part` is one building on the land
        gable_building(part, ...)

The building's floor goes to the lowest land under and along its footprint (terrain.footprint_base), so
nothing floats on the low side and the high side runs into the slope. Its walls' feet (the points at
z <= 0) go down to that level, or stay at the turf's level where the land is higher, so a building
never shows a gap under it whichever ground it stands on."""
import os
import sys
import numpy as np
import nwlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "terrain"))
import terrain  # noqa: E402

T = terrain.load("norwood")
LAST = [0.0]          # the last building's floor level (for roof fittings added after it)


def _hull(pts):
    from scipy.spatial import ConvexHull
    p = np.unique(np.round(np.asarray(pts, float), 2), axis=0)
    if len(p) < 3:
        return [tuple(q) for q in p]
    return [tuple(p[i]) for i in ConvexHull(p).vertices]


def shift(part, n0, base):
    """Lift (or lower) every face added to `part` since index n0 by base; feet at z <= 0 go to min(0, base)."""
    faces = nwlib.PARTS.get(part, [])
    for i in range(n0, len(faces)):
        pts, mat, uv = faces[i]
        new = []
        for p in pts:
            q = np.array(p, float)
            q[2] = min(0.0, base) if q[2] <= 1e-6 else q[2] + base
            new.append(q)
        faces[i] = (new, mat, uv)


class on_land:
    def __init__(self, part, level=None):
        self.part, self.level = part, level

    def __enter__(self):
        self.n0 = len(nwlib.PARTS.get(self.part, []))
        return self

    def __exit__(self, *exc):
        if exc[0]:
            return False
        faces = nwlib.PARTS.get(self.part, [])[self.n0:]
        if not faces:
            return False
        if self.level is not None:
            base = self.level
        else:
            low = [p[:2] for f in faces for p in f[0] if p[2] <= 0.5]
            if len(low) < 3:
                low = [p[:2] for f in faces for p in f[0]]
            base = float(T.footprint_base(_hull(low)))
        LAST[0] = base
        shift(self.part, self.n0, base)
        return False
