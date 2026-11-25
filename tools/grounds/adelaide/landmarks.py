"""The landmarks round Adelaide Oval in 3D (Adelaide to the MCG standard, stage 6): the Adelaide Oval
footbridge over Torrens Lake, the other bridges (King William Road, the University footbridge, the weir), and
St Peter's Cathedral's twin spires north of the ground, and the Memorial Drive tennis canopy west of it (Google Earth). Shapes from their OpenStreetMap outlines; heights
from OSM (the cathedral's 51 m) and the published figures (the footbridge: 255 m, 2014, a white steel deck
that rises over the lake with a sculpted balustrade). Writes assets/grounds/adelaide/landmarks.glb in the
model's frame (x east, y north, z up in Blender; the model's 0, 0 as tools/grounds/adelaide/surrounds.py).

    python3 tools/grounds/adelaide/landmarks.py map.osm      (pip bpy)

Map data (c) OpenStreetMap contributors, ODbL. Looks only.
"""
import math
import os
import sys
import xml.etree.ElementTree as ET

import bpy  # noqa: I001 (bpy first: it provides bmesh and mathutils)
import bmesh
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from surrounds import xy  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "grounds", "adelaide", "landmarks.glb")
FOOTBRIDGE = ["273199895", "848653569"]    # the walkway, the oval's plaza to the Riverbank (south bank)
ROAD_BRIDGES = {"4681589": 22.0, "229146216": 22.0, "751506981": 22.0}   # King William Road over the river
FOOT_BRIDGES = {"185409885": 4.0, "197732389": 4.0}                     # University footbridge, the weir walk
CATHEDRAL = "181219964"


def load(path):
    r = ET.parse(path).getroot()
    nodes = {n.get("id"): xy(float(n.get("lat")), float(n.get("lon"))) for n in r.findall("node")}
    ways = {}
    for w in r.findall("way"):
        t = {x.get("k"): x.get("v") for x in w.findall("tag")}
        ways[w.get("id")] = (t, [nodes[nd.get("ref")] for nd in w.findall("nd") if nd.get("ref") in nodes])
    return ways


def material(name, rgb, rough=0.8, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*[c ** 2.2 for c in rgb], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def quad(bm, a, b, c, d):
    bm.faces.new([bm.verts.new(p) for p in (a, b, c, d)])


def prism(bm, pts, z0, z1):
    """A closed outline (x, y) extruded from z0 to z1."""
    pts = list(pts)
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    a = np.array(pts)
    if 0.5 * np.sum(a[:, 0] * np.roll(a[:, 1], -1) - np.roll(a[:, 0], -1) * a[:, 1]) < 0:
        pts = pts[::-1]
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]
    hi = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(hi)
    bm.faces.new(lo[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])


def path_fn(path):
    p = np.array(path, float)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])

    def at(d):
        return Vector((float(np.interp(d, s, p[:, 0])), float(np.interp(d, s, p[:, 1])), 0.0))

    def side(d):
        a, b = at(max(d - 1.0, 0.0)), at(min(d + 1.0, s[-1]))
        t = (b - a).normalized()
        return Vector((-t.y, t.x, 0.0))
    return at, side, float(s[-1])


def deck_along(bm, path, width, zfn, depth, n=None):
    """A deck of `width` along `path`, top at zfn(d), `depth` deep (a closed box section)."""
    at, side, L = path_fn(path)
    n = n or max(2, int(L / 2.0))
    prev = None
    for i in range(n + 1):
        d = L * i / n
        c, sd, z = at(d), side(d), zfn(d, L)
        q = [bm.verts.new(c + sd * width / 2 + Vector((0, 0, z))), bm.verts.new(c - sd * width / 2 + Vector((0, 0, z))),
             bm.verts.new(c - sd * width / 2 * 0.8 + Vector((0, 0, z - depth))),
             bm.verts.new(c + sd * width / 2 * 0.8 + Vector((0, 0, z - depth)))]
        if prev:
            for k in range(4):
                j = (k + 1) % 4
                bm.faces.new([prev[k], prev[j], q[j], q[k]])
        else:
            bm.faces.new(q[::-1])
        prev = q
    bm.faces.new(prev)
    return at, side, L


def footbridge(ways, bm_deck, bm_white, bm_steel):
    """Adelaide Oval footbridge: 6 m deck rising about 3 m over the lake, each side a white sculpted balustrade
    that leans out and rises at mid-span, steel box girder under it, two piers in the lake."""
    path = []
    for wid in FOOTBRIDGE:
        pts = ways[wid][1]
        path += pts if not path else pts[1:]
    zf = lambda d, L: 4.0 + 3.0 * math.sin(math.pi * d / L)
    at, side, L = deck_along(bm_deck, path, 6.0, zf, 0.4)
    # the girder under the deck
    deck_along(bm_steel, path, 4.2, lambda d, L: zf(d, L) - 0.4, 1.2)
    # balustrade: a white ribbon each side, 1.3 m at the ends to 1.9 m mid-span, leaning out 0.35 m
    n = int(L / 1.5)
    for s in (1, -1):
        prev = None
        for i in range(n + 1):
            d = L * i / n
            c, sd, z = at(d), side(d) * s, zf(d, L)
            h = 1.3 + 0.6 * math.sin(math.pi * d / L)
            q = [bm_white.verts.new(c + sd * 3.0 + Vector((0, 0, z - 0.9))),
                 bm_white.verts.new(c + sd * 3.35 + Vector((0, 0, z + h))),
                 bm_white.verts.new(c + sd * 3.15 + Vector((0, 0, z + h))),
                 bm_white.verts.new(c + sd * 2.85 + Vector((0, 0, z - 0.9)))]
            if prev:
                for k in range(4):
                    j = (k + 1) % 4
                    bm_white.faces.new([prev[k], prev[j], q[j], q[k]])
            prev = q
    for f in (0.36, 0.64):
        c = at(L * f)
        prism(bm_steel, [(c.x - 1.2, c.y - 1.2), (c.x + 1.2, c.y - 1.2), (c.x + 1.2, c.y + 1.2), (c.x - 1.2, c.y + 1.2)],
              -2.0, zf(L * f, L) - 1.6)


def flat_bridge(ways, wid, width, z, bm_deck, bm_rail):
    path = ways[wid][1]
    if len(path) < 2:
        return
    at, side, L = path_fn(path)
    deck_along(bm_deck, path, width, lambda d, ln: z, 1.4, n=max(2, int(L / 4)))
    for s in (1, -1):
        deck_along(bm_rail, [tuple(at(d) + side(d) * s * (width / 2 - 0.2))[:2] for d in np.linspace(0, L, max(2, int(L / 4)))],
                   0.35, lambda d, ln: z + 1.1, 1.1)


def cathedral(ways, bm_stone, bm_roof, bm_spire):
    """St Peter's: a sandstone nave and apse to the north-west (the footprint), a slate roof, and the
    two towers at the south-east front, their spires to 51 m."""
    ring = ways[CATHEDRAL][1]
    prism(bm_stone, ring, 0.0, 17.0)
    a = np.array(ring[:-1])
    front = a[np.argsort(-(a @ np.array([0.62, -0.78])))[:2]]   # the two south-east corners
    back = a[np.argsort(a @ np.array([0.62, -0.78]))[:3]].mean(0)
    f0, f1 = front
    mid = (f0 + f1) / 2
    ax = (back - mid) / np.linalg.norm(back - mid)
    sd = np.array([-ax[1], ax[0]])
    L = float(np.linalg.norm(back - mid))
    # nave roof: a ridge 27 m high along the axis, eaves at 17 m, 16 m span
    for t0, t1 in ((14.0, L - 6.0),):
        for s in (1, -1):
            e0 = mid + ax * t0 + sd * 8.0 * s
            e1 = mid + ax * t1 + sd * 8.0 * s
            r0 = mid + ax * t0
            r1 = mid + ax * t1
            quad(bm_roof, (*e0, 17.0), (*e1, 17.0), (*r1, 27.0), (*r0, 27.0))
    # towers: 9 m square at each front corner, to 36 m, then an octagonal spire to 51 m
    for f in (f0, f1):
        c = f + ax * 4.5 + (sd if (f - mid) @ sd > 0 else -sd) * -4.5
        sq = [(p[0], p[1]) for p in [(c + ax * 4.5 * i + sd * 4.5 * j) for i, j in ((1, 1), (1, -1), (-1, -1), (-1, 1))]]
        prism(bm_stone, sq, 0.0, 36.0)
        base = [bm_spire.verts.new((c[0] + 4.3 * math.cos(k * math.pi / 4), c[1] + 4.3 * math.sin(k * math.pi / 4), 36.0)) for k in range(8)]
        tip = bm_spire.verts.new((c[0], c[1], 51.0))
        for k in range(8):
            bm_spire.faces.new([base[k], base[(k + 1) % 8], tip])
        # four corner pinnacles
        for i, j in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
            p = c + ax * 4.0 * i + sd * 4.0 * j
            b = [bm_spire.verts.new((p[0] + 0.6 * math.cos(k * math.pi / 2), p[1] + 0.6 * math.sin(k * math.pi / 2), 36.0)) for k in range(4)]
            tp = bm_spire.verts.new((p[0], p[1], 40.0))
            for k in range(4):
                bm_spire.faces.new([b[k], b[(k + 1) % 4], tp])


# The Memorial Drive tennis centre's show-court canopy west of the ground, from Google Earth (straight down from 400 m
# and oblique from 180 m, 2026-11-22, the calibrated camera of tools/grounds/ge_compare.py): a white pillow roof
# about 40 x 41 m on slim steel columns, its edge about 9 m up and its crown a metre higher, with a flat-roofed glazed
# annex on its west side. OSM has only a 20 x 26 m "roof" here (way 1238356686, left out of buildings.bin).
TENNIS = {"c": (-138.0, -103.0), "a": 20.0, "b": 20.5, "rot": -2.5, "edge": 9.0, "crown": 1.2,
          "annex": [(-169.7, -89.8), (-152.8, -89.8), (-152.8, -123.3), (-169.7, -123.3)], "annex_h": 6.0}


def tennis_canopy(bm_white, bm_steel, bm_glass):
    t = TENNIS; cx, cy = t["c"]; r_ = math.radians(t["rot"]); cr, sr = math.cos(r_), math.sin(r_)
    rot = lambda x, y: (cx + x * cr - y * sr, cy + x * sr + y * cr)
    def at(r, th, dz=0.0):   # a superellipse (rounded square) ring r of the roof, 0 centre .. 1 edge
        c, s_ = math.cos(th), math.sin(th)
        u = math.copysign(abs(c) ** 0.5, c); v = math.copysign(abs(s_) ** 0.5, s_)
        x, y = rot(t["a"] * r * u, t["b"] * r * v)
        return (x, y, t["edge"] + t["crown"] * (1 - r * r) + dz)
    NA, NR = 64, 8
    ths = [2 * math.pi * i / NA for i in range(NA)]
    for dz, flip in ((0.0, False), (-0.45, True)):   # the top and, 45 cm under it, the underside
        rings = [[bm_white.verts.new(at(r / NR, th, dz)) for th in ths] for r in range(1, NR + 1)]
        top = bm_white.verts.new(at(0, 0, dz))
        for i in range(NA):
            f = [top, rings[0][i], rings[0][(i + 1) % NA]]
            bm_white.faces.new(f[::-1] if flip else f)
        for k in range(NR - 1):
            for i in range(NA):
                f = [rings[k][i], rings[k + 1][i], rings[k + 1][(i + 1) % NA], rings[k][(i + 1) % NA]]
                bm_white.faces.new(f[::-1] if flip else f)
    for i in range(NA):   # the fascia round the edge
        a, b = at(1, ths[i]), at(1, ths[(i + 1) % NA])
        quad(bm_white, (a[0], a[1], a[2] - 0.45), (b[0], b[1], b[2] - 0.45), b, a)
    for i in range(10):   # slim columns just inside the edge
        x, y, z = at(0.9, 2 * math.pi * (i + 0.5) / 10)
        prism(bm_steel, [(x - 0.2, y - 0.2), (x + 0.2, y - 0.2), (x + 0.2, y + 0.2), (x - 0.2, y + 0.2)], 0.0, z - 0.4)
    prism(bm_glass, t["annex"], 0.0, t["annex_h"] - 0.6)          # the annex: dark glass walls
    prism(bm_white, t["annex"], t["annex_h"] - 0.6, t["annex_h"])  # its pale flat roof and fascia


def main():
    ways = load(sys.argv[1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    parts = {"bridge_deck": (material("bridge_deck", (0.78, 0.77, 0.74)), bmesh.new()),
             "bridge_white": (material("bridge_white", (0.95, 0.95, 0.93), 0.5), bmesh.new()),
             "bridge_steel": (material("bridge_steel", (0.62, 0.63, 0.64), 0.6, 0.2), bmesh.new()),
             "cathedral_stone": (material("cathedral_stone", (0.66, 0.58, 0.47), 0.9), bmesh.new()),
             "cathedral_roof": (material("cathedral_roof", (0.33, 0.35, 0.37), 0.8), bmesh.new()),
             "cathedral_spire": (material("cathedral_spire", (0.6, 0.53, 0.44), 0.9), bmesh.new())}
    footbridge(ways, parts["bridge_deck"][1], parts["bridge_white"][1], parts["bridge_steel"][1])
    for wid, w in ROAD_BRIDGES.items():
        flat_bridge(ways, wid, w, 3.0, parts["bridge_deck"][1], parts["bridge_white"][1])
    for wid, w in FOOT_BRIDGES.items():
        flat_bridge(ways, wid, w, 2.5, parts["bridge_deck"][1], parts["bridge_steel"][1])
    cathedral(ways, parts["cathedral_stone"][1], parts["cathedral_roof"][1], parts["cathedral_spire"][1])
    parts["tennis_roof"] = (material("tennis_roof", (0.93, 0.93, 0.91), 0.6), bmesh.new())
    parts["tennis_glass"] = (material("tennis_glass", (0.22, 0.27, 0.30), 0.2, 0.1), bmesh.new())
    tennis_canopy(parts["tennis_roof"][1], parts["bridge_steel"][1], parts["tennis_glass"][1])
    for name, (mat, bm) in parts.items():
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        me.materials.append(mat)
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(OUT), export_format="GLB", export_apply=True)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
