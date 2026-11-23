"""The bridges round Optus Stadium, in 3D (Optus rebuild, stage 6): Matagarup Bridge's two white
arches over the Swan, and the Windan, Goongoongup and smaller bridges as decks on piers, from their
OpenStreetMap outlines (man_made=bridge). Writes assets/grounds/optus/bridges.glb in the model's
frame (x east, y north, z up in Blender; the model's 0, 0 as tools/grounds/optus/surrounds.py).

    python3 tools/grounds/optus/bridges.py map.osm      (pip bpy)

Matagarup Bridge: 370 m between its abutments, two 72 m arches that rise from each bank and meet
at deck level mid-river, the deck hung from them on cables (Main Roads WA's published figures).
Map data (c) OpenStreetMap contributors, ODbL.
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

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "grounds", "optus", "bridges.glb")
MATAGARUP_PATH = "404705281"     # the bridge's walkway, abutment to abutment
MATAGARUP_OUTLINE = "758076375"
DECK = {"273472112": 8.5, "273472115": 8.0}   # Windan (Graham Farmer Freeway), Goongoongup (rail)
SMALL_DECK = 4.0


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


def box(bm, centre, axis, length, width, z0, z1):
    ax = Vector((axis[0], axis[1], 0)).normalized()
    sd = Vector((-ax.y, ax.x, 0))
    c = Vector((centre[0], centre[1], 0))
    pts = [c + ax * (length / 2) * i + sd * (width / 2) * j for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    lo = [bm.verts.new((p.x, p.y, z0)) for p in pts]
    hi = [bm.verts.new((p.x, p.y, z1)) for p in pts]
    bm.faces.new(hi)
    bm.faces.new(lo[::-1])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])


def slab(bm, ring, z0, z1):
    """The outline extruded from z0 to z1 (top and bottom as one face each; the exporter triangulates)."""
    pts = ring[:-1] if ring[0] == ring[-1] else ring
    if _signed_area(pts) < 0:
        pts = pts[::-1]
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]
    hi = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(hi)
    bm.faces.new(lo[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])


def _signed_area(p):
    a = np.array(p)
    return 0.5 * np.sum(a[:, 0] * np.roll(a[:, 1], -1) - np.roll(a[:, 0], -1) * a[:, 1])


def axis_of(ring):
    a = np.array(ring[:-1])
    c = a.mean(0)
    u, s, vt = np.linalg.svd(a - c)
    ax = vt[0]
    t = (a - c) @ ax
    w = (a - c) @ vt[1]
    return c, ax, t.min(), t.max(), w.max() - w.min()


def piers(bm, ring, deck_z, step=38.0):
    c, ax, t0, t1, width = axis_of(ring)
    n = max(1, int((t1 - t0) / step))
    for k in range(1, n):
        p = c + ax * (t0 + (t1 - t0) * k / n)
        box(bm, p, ax, 2.2, max(2.0, width * 0.75), -2.0, deck_z - 1.6)


def tube(bm, path, radius, sides=8):
    """A tube along a list of 3D points."""
    rings = []
    for i, p in enumerate(path):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, len(path) - 1)]
        t = (b - a).normalized()
        n = t.cross(Vector((0, 0, 1)))
        if n.length < 1e-4:
            n = Vector((1, 0, 0))
        n.normalize()
        bn = t.cross(n)
        rings.append([bm.verts.new(p + (n * math.cos(2 * math.pi * k / sides) + bn * math.sin(2 * math.pi * k / sides)) * radius)
                      for k in range(sides)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(sides):
            j = (k + 1) % sides
            bm.faces.new([r0[k], r0[j], r1[j], r1[k]])


def matagarup(bm_deck, bm_arch, bm_cable, path):
    p = np.array(path)
    seg = np.hypot(*np.diff(p, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = s[-1]

    def at(d):
        return Vector((float(np.interp(d, s, p[:, 0])), float(np.interp(d, s, p[:, 1])), 0.0))

    def deck_z(d):
        return 3.5 + 3.0 * math.sin(math.pi * d / L)

    # Deck: 9 m wide, 1.4 m deep, following the walkway with a gentle rise to mid-river.
    n = 80
    left, right = [], []
    for i in range(n + 1):
        d = L * i / n
        a, b = at(max(d - 1, 0)), at(min(d + 1, L))
        t = (b - a).normalized()
        sd = Vector((-t.y, t.x, 0))
        c = at(d)
        z = deck_z(d)
        left.append((c + sd * 4.5, z))
        right.append((c - sd * 4.5, z))
    prev = None
    for (l, zl), (r, zr) in zip(left, right):
        q = [bm_deck.verts.new((l.x, l.y, zl)), bm_deck.verts.new((r.x, r.y, zr)),
             bm_deck.verts.new((r.x, r.y, zr - 1.4)), bm_deck.verts.new((l.x, l.y, zl - 1.4))]
        if prev:
            for k in range(4):
                j = (k + 1) % 4
                bm_deck.faces.new([prev[k], prev[j], q[j], q[k]])
        prev = q
    # Arches: each 72 m high, from an abutment to mid-river, where the two meet at the deck.
    # The 30 m of each end the walkway runs over land are left to the abutment.
    a0, mid, a1 = 25.0, L / 2, L - 25.0
    for lo, hi in ((a0, mid), (mid, a1)):
        pts = []
        for i in range(41):
            u = i / 40
            d = lo + (hi - lo) * u
            pts.append(at(d) + Vector((0, 0, deck_z(d) + 66.0 * math.sin(math.pi * u) ** 0.85)))
        tube(bm_arch, pts, 1.6)
        # Hangers to both deck edges every 9 m.
        for i in range(1, int((hi - lo) / 9)):
            d = lo + 9 * i
            u = (d - lo) / (hi - lo)
            top = at(d) + Vector((0, 0, deck_z(d) + 66.0 * math.sin(math.pi * u) ** 0.85))
            a, b = at(max(d - 1, 0)), at(min(d + 1, L))
            t = (b - a).normalized()
            sd = Vector((-t.y, t.x, 0))
            for side in (1, -1):
                foot = at(d) + sd * 4.3 * side + Vector((0, 0, deck_z(d)))
                tube(bm_cable, [top, foot], 0.12, sides=4)
    # Abutments and the mid-river pier where the arches meet.
    for d in (a0, mid, a1):
        a, b = at(max(d - 1, 0)), at(min(d + 1, L))
        box(bm_deck, at(d), (b - a).to_2d(), 6.0, 11.0, -2.0, deck_z(d) - 1.4)


def main():
    ways = load(sys.argv[1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    parts = {"bridge_deck": (material("bridge_deck", (0.74, 0.72, 0.68)), bmesh.new()),
             "bridge_arch": (material("bridge_arch", (0.93, 0.93, 0.91), 0.5), bmesh.new()),
             "bridge_cable": (material("bridge_cable", (0.55, 0.56, 0.57), 0.5, 0.5), bmesh.new())}
    deck = parts["bridge_deck"][1]
    matagarup(deck, parts["bridge_arch"][1], parts["bridge_cable"][1], ways[MATAGARUP_PATH][1])
    for wid, (t, ring) in ways.items():
        if t.get("man_made") != "bridge" or wid == MATAGARUP_OUTLINE or len(ring) < 4 or ring[0] != ring[-1]:
            continue
        a = np.array(ring)
        if np.abs(a).max() > 950:
            continue
        z = DECK.get(wid, SMALL_DECK)
        slab(deck, ring, z - 1.8, z)
        piers(deck, ring, z)
    for name, (mat, bm) in parts.items():
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        me.materials.append(mat)
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(OUT), export_format="GLB", export_apply=True)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
