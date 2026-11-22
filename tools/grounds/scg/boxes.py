"""The SCG's corporate boxes: the glazed band at the back of each stand's top tier (SCG rebuild, 2026-11-22).

From the field the model (#1909) showed a blank stand back wall, 6-12 m of it, between the top row of seats
and the roof, seen from inside where nothing was drawn for it. Google Earth and the photos show the band
under each roof as dark glazing over a pale parapet: the boxes and the members' glass. This finds that
gap round the bowl and closes it with a band, drawn through GroundModels.PARTS:

- per half degree, a ray from the pitch centre out over the top seats finds the back wall the model shows
  from inside (material `wall`, `facade` or `cladl` hit from behind);
- the seats' top row there (seats_*.bin) is the band's foot, a ray up finds the roof's underside;
- a pale parapet 1.1 m high, then dark glass with a mullion every 2.4 m to the underside, 0.25 m in
  front of the wall.

    python3 tools/grounds/scg/boxes.py

Writes assets/grounds/scg/boxes.bin: triangles, per vertex x, y, z, normal, colour (float32, model metres).
"""
import math
import os

import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg")
PC = np.array([0.94, 11.82])
BACK = ("wall", "facade", "cladl")
PARAPET = (0.74, 0.73, 0.70)
GLASS = (0.13, 0.15, 0.18)
MULLION = (0.30, 0.31, 0.33)
STEP = 0.5          # degrees
MULLION_EVERY = 2.4


def meshes():
    out = []
    for f in ("scg_part1.glb", "scg_part2.glb"):
        s = trimesh.load(os.path.join(DIR, f))
        for g in s.geometry.values():
            out.append((g.visual.material.name, g))
    return out


def seats():
    pts = []
    for f in os.listdir(DIR):
        if f.startswith("seats_") and f.endswith(".bin"):
            a = np.fromfile(os.path.join(DIR, f), "<f4").reshape(-1, 12)
            pts.append(a[:, [3, 7, 11]])
    return np.concatenate(pts)


def cast(ms, o, d):
    best = None
    for name, g in ms:
        loc, _ri, fi = g.ray.intersects_location([o], [d])
        for p, f in zip(loc, fi):
            dist = float(np.linalg.norm(p - o))
            if dist > 0.05 and (best is None or dist < best[0]):
                best = (dist, name, p, g.face_normals[f])
    return best


def main():
    ms = meshes()
    st = seats()
    sa = np.degrees(np.arctan2(-(st[:, 2] - PC[1]), st[:, 0] - PC[0]))
    sr = np.hypot(st[:, 0] - PC[0], st[:, 2] - PC[1])
    cols = []
    for a in np.arange(-180.0, 180.0, STEP):
        m = np.abs(((sa - a + 180) % 360) - 180) < 1.0
        if m.sum() < 5:
            cols.append(None)
            continue
        top = float(st[m, 1].max())
        rtop = float(sr[m][np.argmax(st[m, 1])])
        rad = math.radians(a)
        d = np.array([math.cos(rad), 0.0, -math.sin(rad)])
        o = np.array([PC[0], top + 1.6, PC[1]]) + d * (rtop - 2.0)
        hit = cast(ms, o, d)
        if hit is None or hit[1] not in BACK or hit[3] @ d < 0.2 or hit[0] > 12.0:
            cols.append(None)          # no back wall seen from behind just past the top row
            continue
        rw = rtop - 2.0 + hit[0] - 0.25
        up = cast(ms, np.array([PC[0], top + 0.5, PC[1]]) + d * (rw - 0.6), np.array([0.0, 1.0, 0.0]))
        y1 = float(up[2][1]) if up is not None and up[0] < 25.0 else top + 8.0
        if y1 - top < 2.0:
            cols.append(None)
            continue
        cols.append((a, rw, top + 0.2, y1))
    tris = []

    def quad(p0, p1, p2, p3, n, c):
        for t in ((p0, p1, p2), (p0, p2, p3)):
            for p in t:
                tris.extend(list(p) + list(n) + list(c))

    run = 0.0
    for c0, c1 in zip(cols, cols[1:]):
        if c0 is None or c1 is None:
            continue
        pts = []
        for a, rw, y0, y1 in (c0, c1):
            rad = math.radians(a)
            pts.append((PC[0] + rw * math.cos(rad), PC[1] - rw * math.sin(rad), y0, y1))
        (x0, z0, b0, t0), (x1, z1, b1, t1) = pts
        n = np.array([-(x0 + x1) / 2 + PC[0], 0.0, -(z0 + z1) / 2 + PC[1]])
        n /= np.linalg.norm(n)
        seg = math.hypot(x1 - x0, z1 - z0)
        p0, p1 = min(b0 + 1.1, t0), min(b1 + 1.1, t1)
        quad((x0, b0, z0), (x1, b1, z1), (x1, p1, z1), (x0, p0, z0), n, PARAPET)
        quad((x0, p0, z0), (x1, p1, z1), (x1, t1, z1), (x0, t0, z0), n, GLASS)
        # mullions: thin pale strips standing 3 cm proud
        k0 = math.ceil(run / MULLION_EVERY)
        while k0 * MULLION_EVERY < run + seg:
            f = (k0 * MULLION_EVERY - run) / seg
            xm, zm = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
            tx, tz = (x1 - x0) / seg * 0.06, (z1 - z0) / seg * 0.06
            ox, oz = n[0] * 0.03, n[2] * 0.03
            pm, tm = p0 + (p1 - p0) * f, t0 + (t1 - t0) * f
            quad((xm - tx + ox, pm, zm - tz + oz), (xm + tx + ox, pm, zm + tz + oz),
                 (xm + tx + ox, tm, zm + tz + oz), (xm - tx + ox, tm, zm - tz + oz), n, MULLION)
            k0 += 1
        run += seg
    arr = np.array(tris, "<f4")
    arr.tofile(os.path.join(DIR, "boxes.bin"))
    print("boxes.bin: %d columns of %d, %d triangles" % (sum(c is not None for c in cols), len(cols), len(arr) // 27))


if __name__ == "__main__":
    main()
