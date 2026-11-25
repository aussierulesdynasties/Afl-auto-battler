#!/usr/bin/env python3
"""Mesh-level overlap check for a two-man clip, on skin_pair.gd's skinned bodies.

    python3 tools/oval3d/check_mesh_pair.py SKIN_DIR [FROM TO] [--depth CM]

For every frame, each man's vertices are tested against the other man's body with the
generalised winding number (robust for a body mesh made of several open parts: inside is about
1, outside about 0). A vertex inside the other man is skin or kit through his body. Its depth is
its distance to the other man's surface. Prints, per frame, how many vertices are inside and the
deepest, with the body part (nearest of a few named landmarks), and a verdict line:
PASS when no vertex is deeper than --depth (default 1.0 cm: cloth and flesh pressing together).
"""
import glob
import os
import sys

import igl
import numpy as np


def load(d, tag, n, nv):
    return np.fromfile(os.path.join(d, "%s_%d.f32" % (tag, n)), dtype="<f4").reshape(nv, 3).astype(np.float64)


def main():
    a = sys.argv[1:]
    d = a[0]
    lim = float(a[a.index("--depth") + 1]) / 100.0 if "--depth" in a else 0.01
    faces = np.fromfile(os.path.join(d, "faces.i32"), dtype="<i4").reshape(-1, 3)
    nv = int(faces.max()) + 1
    frames = sorted(int(os.path.basename(p)[2:-4]) for p in glob.glob(os.path.join(d, "a_*.f32")))
    if len(a) > 2 and not a[1].startswith("--"):
        frames = [f for f in frames if int(a[1]) <= f <= int(a[2])]
    worst = (0.0, -1, "")
    bad = []
    for n in frames:
        va = load(d, "a", n, nv)
        vb = load(d, "b", n, nv)
        line = []
        for (who, pts, other, oname) in (("jumper", va, vb, "stepladder"), ("stepladder", vb, va, "jumper")):
            # Only points near the other man need the winding number.
            lo, hi = other.min(0) - 0.02, other.max(0) + 0.02
            near = np.all((pts > lo) & (pts < hi), axis=1)
            idx = np.nonzero(near)[0]
            if idx.size == 0:
                continue
            w = igl.fast_winding_number(other, faces, pts[idx])
            # Godot winds front faces clockwise, so inside reads about -1: take the size.
            inside = idx[np.abs(w) > 0.5]
            if inside.size == 0:
                continue
            dist, _, _ = igl.point_mesh_squared_distance(pts[inside], other, faces)
            dist = np.sqrt(dist)
            k = int(np.argmax(dist))
            deep = float(dist[k])
            p = pts[inside[k]]
            line.append("%s into %s: %d verts, deepest %.1f cm at (%.2f, %.2f, %.2f)" % (
                who, oname, inside.size, 100 * deep, p[0], p[1], p[2]))
            if deep > worst[0]:
                worst = (deep, n, who)
            if deep > lim:
                bad.append(n)
        if line:
            print("frame %d: %s" % (n, "; ".join(line)))
    print("VERDICT %s: deepest %.1f cm (frame %d, %s); frames over %.1f cm: %s" % (
        "PASS" if not bad else "FAIL", 100 * worst[0], worst[1], worst[2], 100 * lim, sorted(set(bad))))


if __name__ == "__main__":
    main()
