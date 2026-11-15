"""Export downloaded MakeHuman hair (CC0, MPFB's hair library) for the 3D oval: one GLB, one mesh
per Club Forge style, each on the head bone of the same rig player_average.glb carries.

blender --background --python export_mh_hair_glb.py -- BODY_TYPES.json TYPE OUT.glb STYLE=ASSET [...]
STYLE is a Club Forge id (Appearance.HAIR_STYLES), ASSET a folder in MPFB's data/hair. MPFB fits
each asset to the same body export_player_glb.py builds (its own .mhclo proxy fit), so it sits on
that body's head as its author made it. The mesh keeps its UVs: the game draws it with the
asset's own strand texture, greyed and tinted his hair colour (tools/oval3d/grey_hair_tex.py).
"""
import json, os, sys, time
import bpy

PIPE = os.environ.get("ARD_PIPELINE_BLENDER", os.path.join(os.path.dirname(__file__), "..", "..", "..", "ard-asset-pipeline", "tools", "blender"))
sys.path.insert(0, PIPE)
import ard_body

t0 = time.time()
argv = sys.argv[sys.argv.index("--") + 1:]
presets, body_type, out = json.load(open(argv[0])), argv[1], argv[2]
pairs = [a.split("=", 1) for a in argv[3:]]
hair_dir = os.path.join(ard_body.ASSETS_DIR, "hair")

bpy.ops.wm.read_homefile(use_empty=True)
basemesh, rig = ard_body.build_body(body_type, presets[body_type]["macros"], targets=presets[body_type].get("targets"),
                                    extras=[os.path.join(hair_dir, a) for _, a in pairs])
names = json.loads(basemesh["extras"])

made = []
for (style, asset), name in zip(pairs, names):
    ob = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        if m.type == "ARMATURE":
            ob.modifiers.remove(m)
        else:
            bpy.ops.object.modifier_apply(modifier=m.name)
    if ob.data.shape_keys:
        ob.shape_key_clear()
    ob.vertex_groups.clear()
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = "head"
    ob.matrix_world = mw
    ob.data.materials.clear()
    ob.data.materials.append(bpy.data.materials.new(f"ARD_hair_{style}"))
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.name = ob.data.name = f"hair_{style}"
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print(f"HAIR {style} <- {asset}: {tris} tris")
    made.append(ob)

bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
for ob in made:
    ob.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True,
                          export_animations=False, export_apply=False, export_yup=True)
print(f"EXPORT {out}: {len(made)} styles in {time.time() - t0:.1f}s")
