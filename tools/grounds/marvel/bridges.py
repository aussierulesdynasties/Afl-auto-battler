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
BOLTE_Z = WATER_Z + 25.0
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


def main():
    ways = load(sys.argv[1:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # round 13 (PC check of round 12, obl_w: a wide white slab where Google Earth shows a dark road): asphalt grey
    parts = {"bridge_deck": (ob.material("bridge_deck", (0.42, 0.43, 0.44)), bmesh.new()),
             "bridge_tower": (ob.material("bridge_tower", (0.78, 0.78, 0.76)), bmesh.new())}
    deck = parts["bridge_deck"][1]
    for wid in BOLTE_TOWERS:
        tower(parts["bridge_tower"][1], ways[wid][1], TOWER_H)
    for wid, (t, ring) in ways.items():
        if t.get("man_made") != "bridge" or len(ring) < 4 or ring[0] != ring[-1]:
            continue
        if np.abs(np.array(ring)).max() > (REACH if wid == BOLTE_DECK else 950):
            continue
        if wid == BOLTE_DECK:
            z = BOLTE_Z
        else:
            pts = np.array(ring, float)
            z = max(float(np.max(land.z(pts[:, 0], pts[:, 1]))), WATER_Z + SMALL_DECK)
        ob.slab(deck, ring, z - 2.5, z)
        ob.piers(deck, ring, z, step=60.0 if wid == BOLTE_DECK else 38.0)
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
