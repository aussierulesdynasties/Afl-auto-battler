"""r15 patch on the game model (assets/grounds/traeger/traeger.glb, r14): the boundary fence on Google Earth's turf edge.

The fence (fence_hoard, fence_rail) was laid on ring_sat.json, a ring picked off a 2020 aerial, which measures 2.8 m
off the turf's edge on average and up to 7.2 m (measure/: three registered straight-down Google Earth shots, one
6-order smooth curve through ~5,800 edge readings, 0.28 m rms). Every vertex of those parts is moved along the
ray from the curve's middle by the gap between the two rings at its bearing, so the fence stands on the fitted
curve (measure/outline_model.json, turf_edge) and keeps its own posts, rails and thickness.

    python fix_r15.py -- in.glb out.glb        (Blender's Python module, bpy 5.2)
"""
import json
import math
import os
import sys

import bpy  # noqa: I001  (bpy first: it puts bmesh and mathutils on the path)
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = ("fence_hoard", "fence_rail")


def polar(P, c):
    """A closed ring (N x 2, model x, z) as radius against bearing about c, for np.interp (periodic)."""
    d = P - c
    t = np.arctan2(d[:, 1], d[:, 0])
    r = np.hypot(d[:, 0], d[:, 1])
    o = np.argsort(t)
    t, r = t[o], r[o]
    return np.r_[t - 2 * math.pi, t, t + 2 * math.pi], np.r_[r, r, r]


a = sys.argv[sys.argv.index('--') + 1:]
O = json.load(open(os.path.join(HERE, "measure", "outline_model.json")))
new = np.array(O["turf_edge"])
old = np.array(json.load(open(os.path.join(HERE, "ring_sat.json"))))
old = np.c_[old[:, 0], -old[:, 1]]                     # (x, north) -> (x, z)
c = new.mean(0)
tn, rn = polar(new, c)
to, ro = polar(old, c)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
moved = 0
for o in bpy.data.objects:
    if o.type != 'MESH' or not any(o.name.startswith(p) for p in PARTS):
        continue
    mw = o.matrix_world
    inv = mw.inverted()
    for v in o.data.vertices:
        w = mw @ v.co                                    # Blender world: (x, -z, y) of glTF
        x, z = w.x, -w.y
        t = math.atan2(z - c[1], x - c[0])
        dr = np.interp(t, tn, rn) - np.interp(t, to, ro)
        w.x += dr * math.cos(t)
        w.y -= dr * math.sin(t)
        v.co = inv @ w
        moved += 1
    o.data.update()
    print('moved', o.name)
print('vertices moved', moved)
bpy.ops.export_scene.gltf(filepath=a[1], export_format='GLB', export_apply=True, export_yup=True)
