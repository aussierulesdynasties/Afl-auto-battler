"""The MCG's roof trusses as real lattice frames (MCG flagship, model rebuild).

The model (build.py, on the director's PC) draws each truss on the east and south roofs as three
single beams: a mast at the roof's back edge, a boom down to the roof, a tie. From Google Earth
they are deep steel lattices, pale grey with a blue light box on each mast. This reads each frame's
mast and boom from the model and builds them again as square lattices, with the back stay
Google Earth shows from each mast's head down to the stand's back wall (four chords, a zigzag brace
on every face), writing assets/grounds/mcg/trusses.bin: per vertex x, y, z, normal, colour (float32,
glTF metres), with the stays that hold the north roofs to their masts. GroundModels.PARTS hides the model's own beams and draws these instead.

    python3 tools/grounds/mcg/trusses.py
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_tris import load  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
GLB = os.path.join(ROOT, "assets", "grounds", "mcg", "mcg.glb")
OUT = os.path.join(ROOT, "assets", "grounds", "mcg", "trusses.bin")

STEEL = (0.84, 0.83, 0.80)     # Google Earth: pale grey, a little blue
NODE = (0.42, 0.62, 0.82)      # the light box at each boom's tip
MAST_W = 2.0                   # lattice section, m a side
BOOM_W = 1.6
CHORD = 0.22
BRACE = 0.12

verts = []


def box(a, b, t, col):
    """A square beam of side t from a to b (12 triangles, flat normals)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = b - a
    ln = np.linalg.norm(d)
    if ln < 1e-4:
        return
    d /= ln
    up = np.array([0.0, 1.0, 0.0]) if abs(d[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(d, up)
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    h = t / 2
    c = [a + (su * u + sv * v) * h for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    c += [p + d * ln for p in c]
    faces = [(0, 1, 5, 4, -v), (1, 2, 6, 5, u), (2, 3, 7, 6, v), (3, 0, 4, 7, -u), (3, 2, 1, 0, -d), (4, 5, 6, 7, d)]
    for i0, i1, i2, i3, n in faces:
        for k in (i0, i1, i2, i0, i2, i3):
            verts.append(list(c[k]) + list(n) + list(col))


def lattice(a, b, w, col=STEEL):
    """A square lattice from a to b, side w: four chords and a zigzag brace on each face."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = b - a
    ln = np.linalg.norm(d)
    d /= ln
    up = np.array([0.0, 1.0, 0.0]) if abs(d[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(d, up)
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    h = w / 2
    corners = [(su * u + sv * v) * h for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for c in corners:
        box(a + c, b + c, CHORD, col)
    n = max(2, int(round(ln / w)))
    for f in range(4):
        c0, c1 = corners[f], corners[(f + 1) % 4]
        for i in range(n):
            p = a + d * (ln * i / n)
            q = a + d * (ln * (i + 1) / n)
            if i % 2 == 0:
                box(p + c0, q + c1, BRACE, col)
            else:
                box(p + c1, q + c0, BRACE, col)


def frames(tris):
    """Each truss frame of the model: (mast foot, mast top, boom foot), glTF metres."""
    P = tris.reshape(-1, 3)
    bear = np.degrees(np.arctan2(P[:, 0], -P[:, 2])) % 360
    order = np.argsort(bear)
    groups, cur = [], [order[0]]
    for i in range(1, len(order)):
        if bear[order[i]] - bear[order[i - 1]] > 1.0:
            groups.append(cur)
            cur = []
        cur.append(order[i])
    groups.append(cur)
    out = []
    for g in groups:
        Q = P[g]
        if Q[:, 1].max() - Q[:, 1].min() < 8.0:
            continue        # the short ties between frames: kept as built (see ties())
        r = np.hypot(Q[:, 0], Q[:, 2])
        top = Q[np.argmax(Q[:, 1])]
        foot = np.array([top[0], Q[:, 1].min(), top[2]])
        front = Q[np.argmin(r)]
        out.append((foot, top, front))
    return out


def ties(tris):
    """The model's own short ties between frames, kept as they are, in the lattice's grey."""
    for t in tris:
        n = np.cross(t[1] - t[0], t[2] - t[0])
        ln = np.linalg.norm(n)
        if ln < 1e-9:
            continue
        for p in t:
            verts.append(list(p) + list(n / ln) + list(STEEL))


def north_stays(masts, roof):
    """The north stands' masts each hold their roof's front edge on a pair of stays (Google Earth:
    pale tubes from each mast's head down to the front edge). The model has the masts only."""
    P = masts.reshape(-1, 3)
    bear = np.degrees(np.arctan2(P[:, 0], -P[:, 2])) % 360
    R = roof.reshape(-1, 3)
    rb = np.degrees(np.arctan2(R[:, 0], -R[:, 2])) % 360
    rr = np.hypot(R[:, 0], R[:, 2])
    order = np.argsort(bear)
    groups, cur = [], [order[0]]
    for i in range(1, len(order)):
        if bear[order[i]] - bear[order[i - 1]] > 1.0:
            groups.append(cur)
            cur = []
        cur.append(order[i])
    groups.append(cur)
    n = 0
    for g in groups:
        Q = P[g]
        if Q[:, 1].max() - Q[:, 1].min() < 20.0:
            continue
        top = Q[np.argmax(Q[:, 1])]
        b = math.degrees(math.atan2(top[0], -top[2])) % 360
        for side in (-1.6, 1.6):
            near = np.abs((rb - (b + side) + 180) % 360 - 180) < 0.8
            if not near.any():
                continue
            k = np.where(near)[0][np.argmin(rr[near])]
            box(top - np.array([0.0, 0.6, 0.0]), R[k], 0.32, STEEL)
            n += 1
    return n


def main():
    _, meshes = load(GLB)
    tris = np.concatenate([t for name, mat, t in meshes if name == "trusses"])
    fr = frames(tris)
    keep = []
    bear = np.degrees(np.arctan2(tris[:, :, 0].mean(1), -tris[:, :, 2].mean(1))) % 360
    tops = np.array([np.degrees(math.atan2(t[0], -t[2])) % 360 for _, t, _ in fr])
    for k, t in enumerate(tris):
        if np.min(np.abs((tops - bear[k] + 180) % 360 - 180)) > 1.0:
            keep.append(t)
    ties(np.array(keep))
    for foot, top, front in fr:
        # The mast's lattice rises from its foot to its top; the boom runs from the mast's head
        # down to its foot on the roof; a light box caps the mast.
        out = np.array([top[0], 0.0, top[2]])
        out /= np.linalg.norm(out)
        lattice(foot - np.array([0.0, 4.0, 0.0]), top, MAST_W)
        head = top - np.array([0.0, MAST_W * 0.5, 0.0])
        lattice(head, front, BOOM_W)
        # The back stay: from the mast's head down and out to the stand's back wall.
        lattice(head, foot + out * 7.0 - np.array([0.0, 3.0, 0.0]), BOOM_W * 0.8)
        # The blue light box at the boom's tip, seen from above as a blue dash at each frame.
        d = (head - front) / np.linalg.norm(head - front)
        box(front - d * 0.5 + np.array([0, 0.9, 0]), front + d * 3.5 + np.array([0, 0.9, 0]), 1.5, NODE)
    masts = np.concatenate([t for name, mat, t in meshes if name == "masts"])
    roof = np.concatenate([t for name, mat, t in meshes if name == "roof"])
    print("north stays", north_stays(masts, roof))
    a = np.array(verts, "<f4")
    a.tofile(OUT)
    print("frames", len(fr), "triangles", len(a) // 3)


if __name__ == "__main__":
    main()
