"""Merge fitted hair sets into the one GLB the 3D oval loads, each cut renamed to its Club Forge style.

blender --background --python merge_hair_glbs.py -- OUT.glb IN.glb [IN.glb ...] -- STYLE=MESH [...]
Every IN is a set from export_mh_hair_glb.py or export_sf_hair_glb.py: our footballer's rig with
hair_* meshes on its head bone. All sets share the body, so each cut keeps its world place and
moves onto the first set's rig. MESH is the cut's mesh name without "hair_" (sf02_10, afro...);
a mesh with no STYLE is left out. Meshes come out as hair_STYLE.
"""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
cut = argv.index("--")
out, ins = argv[0], argv[1:cut]
style_of = {m: s for s, m in (a.split("=", 1) for a in argv[cut + 1:])}

bpy.ops.wm.read_homefile(use_empty=True)
rig = None
made = []
for path in ins:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    if rig is None:
        rig = arm
    for o in new:
        if o.type != "MESH" or not o.name.startswith("hair_"):
            continue
        src = o.name[len("hair_"):].split(".")[0]
        if src not in style_of:
            continue
        mw = o.matrix_world.copy()
        o.parent = rig
        o.parent_type = "BONE"
        o.parent_bone = "head"
        o.matrix_world = mw
        o.name = o.data.name = "hair_" + style_of[src]
        made.append(o)
        print(f"CUT {src} -> {o.name}")
    for o in new:
        if o is not rig and o not in made:
            bpy.data.objects.remove(o, do_unlink=True)

missing = sorted(set(style_of.values()) - {o.name[len("hair_"):] for o in made})
if missing:
    raise SystemExit(f"no mesh for styles {missing}")
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
for o in made:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True,
                          export_animations=False, export_apply=False, export_yup=True)
print(f"EXPORT {out}: {len(made)} styles")
