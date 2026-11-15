"""Export the Club Forge hair styles for the 3D oval: one GLB, one mesh per style, each on the
head bone of the same rig player_average.glb carries.

blender --background --python export_hair_glb.py -- BODY_TYPES.json TYPE OUT.glb STYLE [STYLE ...]
The styles are the pipeline's own procedural shells (hair_lib.py: no downloaded assets), fitted
to the body export_player_glb.py builds (same MPFB body, same kit volume), so each shell sits
over that body's scalp. Godot reads each mesh's place on the head bone from this file and puts
it on every player's own head bone (Oval3D._hair), tinted his hair colour. bald and buzz have
no shell: the body's scalp draws them (oval3d_player.gdshader, scalp).
"""
import json, os, sys, time
import bpy

PIPE = os.environ.get("ARD_PIPELINE_BLENDER", os.path.join(os.path.dirname(__file__), "..", "..", "..", "ard-asset-pipeline", "tools", "blender"))
sys.path.insert(0, PIPE)
import ard_body
import hair_lib

t0 = time.time()
argv = sys.argv[sys.argv.index("--") + 1:]
presets, body_type, out, styles = json.load(open(argv[0])), argv[1], argv[2], argv[3:]
# Per style, triangles after the decimate: 36 players and the umpires each wear one.
TRIS = int(os.environ.get("ARD_HAIR_TRIS", "1200"))

bpy.ops.wm.read_homefile(use_empty=True)
basemesh, rig = ard_body.build_body(body_type, presets[body_type]["macros"], targets=presets[body_type].get("targets"))
# The kit volume with the scalp skin-tight (scalp=False, as the pipeline fits every shell):
# player_average.glb's scalp is 1 cm out, and the game pulls it back in under a shell
# (oval3d_player.gdshader, SCALP_LIFT), so each shell's edge tucks under real skin.
ard_body.assign_kit(basemesh, rig, outfit=presets[body_type].get("outfit", "footballer"), scalp=False)
ard_body.fix_shoulders(basemesh, rig)
head = hair_lib.Head(basemesh, rig)

mat = bpy.data.materials.new("ARD_hair_style")
made = []
for style in styles:
    if hair_lib.STYLES.get(style, "missing") == "missing":
        raise SystemExit(f"HAIR {style}: not a hair_lib style")
    if style in ("bald", "buzz"):
        continue
    ob = hair_lib.build_hair(basemesh, rig, style, head)
    before = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    dec = ob.modifiers.new("decimate", "DECIMATE")
    dec.ratio = min(1.0, TRIS / max(1, before))
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=dec.name)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.name = ob.data.name = f"hair_{style}"
    after = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print(f"HAIR {style}: {before} -> {after} tris")
    made.append(ob)

bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
for ob in made:
    ob.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True,
                          export_animations=False, export_apply=False, export_yup=True)
print(f"EXPORT {out}: {len(made)} styles in {time.time() - t0:.1f}s")
