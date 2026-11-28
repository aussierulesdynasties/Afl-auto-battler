"""The bridges round Marvel Stadium, in 3D (Marvel rebuild, stage 6): the Bolte Bridge's twin towers
and its deck over Victoria Harbour, and Docklands' smaller bridges as decks on piers, from their
OpenStreetMap outlines (man_made=bridge, man_made=tower). Writes assets/grounds/marvel/bridges.glb in
the model's frame (x east, y north, z up in Blender; the model's 0, 0 as tools/grounds/marvel/surrounds.py).

    python3 tools/grounds/marvel/bridges.py map.osm [map.osm ...]      (pip bpy)

The Bolte Bridge (CityLink, 1999): two free-standing 140 m concrete towers either side of the deck,
which carries the motorway about 25 m over the water (VicRoads' published figures). The towers hold
nothing up: they are the city's gateway marker. Map data (c) OpenStreetMap contributors, ODbL.
"""
import os
import sys
import xml.etree.ElementTree as ET

import bpy  # noqa: I001
import bmesh
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util  # noqa: E402


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


xy = _mod("marvel_surrounds", os.path.join(HERE, "surrounds.py")).xy
# Optus's helpers (box, slab, piers, material); its own `from surrounds import xy` needs its folder.
sys.path.insert(0, os.path.join(HERE, "..", "optus"))
ob = _mod("optus_bridges", os.path.join(HERE, "..", "optus", "bridges.py"))
land = _mod("marvel_land", os.path.join(HERE, "land.py"))

OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "marvel", "bridges.glb")
BOLTE_DECK = "205197533"
BOLTE_TOWERS = ["45442788", "45442805"]
# Round 12 (real land, land.py): the water is at sea level, model z -2.6 (it had been the flat ground's z 0); heights
# over the water count from there, and footbridges' decks from the higher of their landings and 4 m over the water.
WATER_Z = -2.6
TOWER_H = WATER_Z + 140.0
SMALL_DECK = 4.0
REACH = 1600.0     # m from the model's middle: the Bolte Bridge is 1.35 km west


def load(paths):
    nodes, ways = {}, {}
    for p in paths:
        r = ET.parse(p).getroot()
        for n in r.findall("node"):
            nodes[n.get("id")] = xy(float(n.get("lat")), float(n.get("lon")))
        for w in r.findall("way"):
            t = {x.get("k"): x.get("v") for x in w.findall("tag")}
            pts = [nodes[nd.get("ref")] for nd in w.findall("nd") if nd.get("ref") in nodes]
            if w.get("id") not in ways or len(pts) > len(ways[w.get("id")][1]):
                ways[w.get("id")] = (t, pts)
    return ways


def tower(bm, ring, h):
    """A tower from its footprint, tapering to 60% at the top."""
    pts = np.array(ring[:-1] if ring[0] == ring[-1] else ring)
    if ob._signed_area(pts.tolist()) < 0:
        pts = pts[::-1]
    c = pts.mean(0)
    lo = [bm.verts.new((x, y, -2.0)) for x, y in pts]
    hi = [bm.verts.new((c[0] + (x - c[0]) * 0.6, c[1] + (y - c[1]) * 0.6, h)) for x, y in pts]
    bm.faces.new(hi)
    bm.faces.new(lo[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])


# Round 17e (backdrop thread's seam view: "a long flat grey shed roof with an open underside on thin legs"; Wikipedia
# "Bolte Bridge" and Structurae 20000634): four spans, 72 - 173 - 173 - 72 m (490 m), the towers' midpoint over the
# middle pier; two independent single-cell prestressed concrete box girders, 15.35 m wide with a 1.15 m gap, of
# variable depth, 2.65 m to 12.7 m (deepest over the piers, balanced cantilever); clearance below about 25 m. OSM's
# outline also takes in the approach viaducts either side, built as 2.65 m girders on piers about every 40 m.
SPANS = (72.0, 173.0, 173.0, 72.0)
GIRDER_W, GIRDER_GAP = 15.35, 1.15
DEPTH_MIN, DEPTH_MAX = 2.65, 12.7
BOLTE_TOP = WATER_Z + 25.0 + DEPTH_MIN      # the deck's top over the water: 25 m clear under the shallowest girder


def _girder_depth(t, piers):
    d = min(abs(t - p) for p in piers)
    return DEPTH_MIN + (DEPTH_MAX - DEPTH_MIN) * max(0.0, 1.0 - d / 86.5) ** 2


def bolte(top_bm, conc_bm, ring, towers, step=4.0):
    """The Bolte Bridge's twin box girders and their piers (see SPANS)."""
    c, ax, t0, t1, _w = ob.axis_of(ring)
    sd = np.array([-ax[1], ax[0]])
    a = np.array(ring, float)
    s = (a - c) @ sd
    mid = 0.5 * (s.min() + s.max())                     # the outline's middle across (the towers stand either side)
    tc = float(np.mean([(np.array(r[:-1]).mean(0) - c) @ ax for r in towers]))   # the towers' midpoint: the middle pier
    piers = [tc - SPANS[1], tc, tc + SPANS[2]]
    ends = [tc - SPANS[1] - SPANS[0], tc + SPANS[2] + SPANS[3]]
    ts = list(np.arange(t0, t1, step)) + [t1]
    half = GIRDER_W / 2
    for side in (-1.0, 1.0):
        off = mid + side * (half + GIRDER_GAP / 2)
        secs = []
        for t in ts:
            main = ends[0] <= t <= ends[1]
            dep = _girder_depth(t, piers) if main else DEPTH_MIN
            bw = 4.2 if main else 4.0
            prof = [(-half, 0.0), (half, 0.0), (half, -0.55), (bw + 0.8, -0.95), (bw, -dep), (-bw, -dep),
                    (-bw - 0.8, -0.95), (-half, -0.55)]
            p0 = c + ax * t + sd * off
            secs.append([conc_bm.verts.new((*(p0 + sd * x), BOLTE_TOP + z)) for x, z in prof])
        tops = [[top_bm.verts.new(tuple(v.co) ) for v in sec[:2]] for sec in secs]
        for i in range(len(secs) - 1):
            A, B = secs[i], secs[i + 1]
            for k in range(1, len(A)):                    # the sides and underside (not the top, k 0 -> 1)
                j = (k + 1) % len(A)
                conc_bm.faces.new([A[k], A[j], B[j], B[k]])
            TA, TB = tops[i], tops[i + 1]
            top_bm.faces.new([TA[0], TB[0], TB[1], TA[1]])
        for sec in (secs[0], secs[-1]):
            conc_bm.faces.new(sec)
        # the parapets: 1.1 m concrete barriers on both edges of each girder
        for e in (-half + 0.2, half - 0.2):
            for i in range(0, len(ts) - 1):
                p_a = c + ax * ts[i] + sd * (off + e)
                p_b = c + ax * ts[i + 1] + sd * (off + e)
                ob.box(conc_bm, (p_a + p_b) / 2, ax, float(ts[i + 1] - ts[i]) + 0.02, 0.4, BOLTE_TOP, BOLTE_TOP + 1.1)
        # the piers: a wall pier under each girder at the three main piers, lighter ones at the ends and on the
        # approach viaducts about every 40 m
        stations = [(p, 5.0, 7.0) for p in piers] + [(e, 3.0, 6.5) for e in ends]
        for lo, hi in ((t0, ends[0]), (ends[1], t1)):
            n = int((hi - lo) / 40.0)
            stations += [(lo + (hi - lo) * k / (n + 1), 2.5, 6.0) for k in range(1, n + 1)] if n > 0 else []
        for t, along, across in stations:
            dep = _girder_depth(t, piers) if ends[0] <= t <= ends[1] else DEPTH_MIN
            ob.box(conc_bm, c + ax * t + sd * off, ax, along, across, -2.0, BOLTE_TOP - dep + 0.05)
    bmesh.ops.recalc_face_normals(conc_bm, faces=conc_bm.faces)
    bmesh.ops.recalc_face_normals(top_bm, faces=top_bm.faces)
    for f in top_bm.faces:                                # the road faces up
        if f.normal.z < 0:
            f.normal_flip()


def main():
    ways = load(sys.argv[1:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # round 13 (PC check of round 12, obl_w: a wide white slab where Google Earth shows a dark road): asphalt grey
    parts = {"bridge_deck": (ob.material("bridge_deck", (0.42, 0.43, 0.44)), bmesh.new()),
             "bridge_tower": (ob.material("bridge_tower", (0.78, 0.78, 0.76)), bmesh.new()),
             "bridge_concrete": (ob.material("bridge_concrete", (0.7, 0.7, 0.68)), bmesh.new())}
    deck = parts["bridge_deck"][1]
    for wid in BOLTE_TOWERS:
        tower(parts["bridge_tower"][1], ways[wid][1], TOWER_H)
    for wid, (t, ring) in ways.items():
        if t.get("man_made") != "bridge" or len(ring) < 4 or ring[0] != ring[-1]:
            continue
        if np.abs(np.array(ring)).max() > (REACH if wid == BOLTE_DECK else 950):
            continue
        if wid == BOLTE_DECK:
            bolte(deck, parts["bridge_concrete"][1], ring, [ways[w][1] for w in BOLTE_TOWERS])
            continue
        pts = np.array(ring, float)
        z = max(float(np.max(land.z(pts[:, 0], pts[:, 1]))), WATER_Z + SMALL_DECK)
        ob.slab(deck, ring, z - 2.5, z)
        ob.piers(deck, ring, z, step=38.0)
    for name, (mat, bm) in parts.items():
        # piers and tower feet (made from -2 m) run down under the water
        for v in bm.verts:
            if v.co.z <= -1.99:
                v.co.z = WATER_Z - 2.0
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        me.materials.append(mat)
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(OUT), export_format="GLB", export_apply=True)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
