"""Export the vignette footballer (MPFB body, kit regions, our own jog and idle) as a rigged GLB.

blender --background --python export_player_glb.py -- BODY_TYPES.json TYPE OUT.glb
Same body, kit and poses the sprite sheets use (build_sprites.py), so the 3D oval copies the
director-passed motion rather than inventing one. One material per kit region (ARD_<region>),
so Godot recolours each club's guernsey, shorts and socks.
"""
import json, math, os, sys, time
import bpy

PIPE = os.environ.get("ARD_PIPELINE_BLENDER", os.path.join(os.path.dirname(__file__), "..", "..", "..", "ard-asset-pipeline", "tools", "blender"))
sys.path.insert(0, PIPE)
import ard_body
from poses import jog, idle, carry

t0 = time.time()
argv = sys.argv[sys.argv.index("--") + 1:]
presets, body_type, out = json.load(open(argv[0])), argv[1], argv[2]

bpy.ops.wm.read_homefile(use_empty=True)
basemesh, rig = ard_body.build_body(body_type, presets[body_type]["macros"], targets=presets[body_type].get("targets"))
ard_body.assign_kit(basemesh, rig, outfit=presets[body_type].get("outfit", "footballer"))
ard_body.fix_shoulders(basemesh, rig)

# The kit's smooth region fields (kit_<region>, the same ones the sprite masks threshold at
# 0.5) packed for Godot: colour = guernsey, shorts, sock, boot; UV2.x = hair. The game's
# shader draws each region where its field passes 0.5, so a hem is a curve, not face steps.
me = basemesh.data
def field(name):
    a = me.attributes.get(name)
    vals = [0.0] * len(me.vertices)
    if a:
        a.data.foreach_get("value", vals)
    return vals
g, sh, so, bo, ha = (field("kit_" + r) for r in ("guernsey", "shorts", "sock", "boot", "hair"))
# Where each vertex sits on the guernsey (ard_body._store_guernsey_coords, the same coordinates
# the sprites' design pass renders): UV = (across from the wearer's right, up from the hem),
# UV2.y = front 1 / back 0. The game draws every club's design and the number from these.
# The body's own texture UVs are unused by the kit shader, so the first layer carries them.
# On the socks (never next to the guernsey) UV.y is instead where the sock band sits: 0..1
# from 17 cm to 11 cm below the knee in the rest pose, as build_sprites.py's maskA draws it.
gu, gv, gf = field("g_u"), field("g_v"), field("g_front")
rest_z, knee_z = field("rest_z"), float(basemesh["knee_z"])
for v in range(len(me.vertices)):
    if so[v] > 0.0:
        gu[v], gv[v] = 0.0, (rest_z[v] - (knee_z - 0.17)) / 0.06
assert me.uv_layers, "the MPFB body has no UV layer to carry the guernsey coordinates"
uv1 = me.uv_layers[0]
col = me.color_attributes.new("kit", "FLOAT_COLOR", "CORNER")
uv2 = me.uv_layers.new(name="kit_hair")
for li, loop in enumerate(me.loops):
    v = loop.vertex_index
    col.data[li].color = (g[v], sh[v], so[v], bo[v])
    uv1.data[li].uv = (gu[v], gv[v])
    uv2.data[li].uv = (ha[v], gf[v])
print(f"GUERNSEY u {min(gu):.2f}..{max(gu):.2f} v {min(gv):.2f}..{max(gv):.2f} front {min(gf):.2f}..{max(gf):.2f}")
me.color_attributes.active_color = col
me.color_attributes.render_color_index = me.color_attributes.find("kit")
t_build = time.time()

# Plain colours per region so the GLB reads sensibly before Godot recolours it.
BASE = {"skin": (0.76, 0.57, 0.45), "hair": (0.15, 0.10, 0.07), "guernsey": (0.8, 0.1, 0.1),
        "trim": (1, 1, 1), "shorts": (1, 1, 1), "sock": (0.8, 0.1, 0.1), "boot": (0.05, 0.05, 0.05)}
for r, c in BASE.items():
    m = bpy.data.materials.get(f"ARD_{r}")
    if m is None:
        continue
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*c, 1)
        bsdf.inputs["Roughness"].default_value = 0.8

rig.animation_data_create()
# While baking, the NLA stays off: otherwise the strips already baked (jog) are re-applied by
# every depsgraph update and the next action's first key is posed on top of them (carry's key 0
# held the hands at the head). On again for the export, which writes one action per track.
rig.animation_data.use_nla = False


def bake(name, fn, frames, fist):
    act = bpy.data.actions.new(name)
    rig.animation_data.action = act
    lows = []
    for i in range(frames + 1):          # last frame = first, so the cycle loops cleanly
        ard_body.pose(rig, fn((i % frames) / frames if frames else 0.0))
        ard_body.curl_fingers(rig, fist)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = basemesh.evaluated_get(dg)
        lows.append(min((ev.matrix_world @ v.co).z for v in ev.data.vertices))
        for pb in rig.pose.bones:
            pb.rotation_mode = "QUATERNION"
            pb.keyframe_insert("rotation_quaternion", frame=i + 1)
            pb.keyframe_insert("location", frame=i + 1)
    track = rig.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, 1, act)
    rig.animation_data.action = None
    print(f"ACTION {name}: {frames + 1} keys, feet low point min {min(lows):.3f} max {max(lows):.3f} m")


bake("jog", jog, 16, 70)
bake("idle", idle, 1, 35)
bake("carry", carry, 16, 10)

# The mocap moves (row 198, "3d view 2" retargets the director's Rokoko takes onto this rig):
# ARD_CLIPS names a .blend whose actions are keyed on this same rig at CLIP_FPS. Each becomes
# its own track; key times are rescaled to this scene's rate so the move keeps its real speed.
# The check poses their rig and ours at the same moment and compares where the hands, feet and
# head land: a rig whose bones were re-oriented on import would bend the limbs differently.
CLIPS = os.environ.get("ARD_CLIPS", "")
CLIP_FPS = 30.0
if CLIPS:
    fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    with bpy.data.libraries.load(CLIPS) as (src, dst):
        dst.actions = list(src.actions)
        dst.objects = [n for n in src.objects]
    theirs = next(o for o in dst.objects if o and o.type == "ARMATURE")
    bpy.context.scene.collection.objects.link(theirs)
    theirs.animation_data_create()
    probe = ("hand_l", "hand_r", "foot_l", "foot_r", "head")

    def keys(act):
        if getattr(act, "layers", None):
            return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
        return list(act.fcurves)

    def slot(holder, act):
        if hasattr(holder, "action_slot") and act.slots:
            holder.action_slot = act.slots[0]

    for act in sorted(dst.actions, key=lambda a: a.name):
        lo, hi = act.frame_range
        worst = 0.0
        for k in range(5):
            f = lo + (hi - lo) * k / 4
            theirs.animation_data.action = act
            slot(theirs.animation_data, act)
            bpy.context.scene.frame_set(int(f))
            a = {b: theirs.matrix_world @ theirs.pose.bones[b].head for b in probe}
            rig.animation_data.action = act
            slot(rig.animation_data, act)
            bpy.context.scene.frame_set(int(f))
            for b in probe:
                worst = max(worst, ((rig.matrix_world @ rig.pose.bones[b].head) - a[b]).length)
        rig.animation_data.action = None
        theirs.animation_data.action = None
        if worst > 0.01:
            raise SystemExit(f"CLIP {act.name}: our rig lands {worst:.3f} m from theirs; bone rests differ")
        s = fps / CLIP_FPS
        for fc in keys(act):
            for kp in fc.keyframe_points:
                kp.co.x = 1 + (kp.co.x - lo) * s
                kp.handle_left.x = 1 + (kp.handle_left.x - lo) * s
                kp.handle_right.x = 1 + (kp.handle_right.x - lo) * s
            fc.update()
        track = rig.animation_data.nla_tracks.new()
        track.name = act.name
        strip = track.strips.new(act.name, 1, act)
        slot(strip, act)
        print(f"CLIP {act.name}: {(hi - lo) / CLIP_FPS:.2f} s, rig match {worst * 1000:.1f} mm")
    bpy.data.objects.remove(theirs)
rig.animation_data.use_nla = True
t_anim = time.time()

bpy.ops.object.select_all(action="DESELECT")
basemesh.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
tris = sum(len(p.vertices) - 2 for p in basemesh.data.polygons)
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True,
                          export_animations=True, export_animation_mode="NLA_TRACKS",
                          export_apply=False, export_yup=True,
                          export_vertex_color="ACTIVE", export_all_vertex_colors=False)
t_end = time.time()
print(f"EXPORT {out} tris={tris} verts={len(basemesh.data.vertices)} "
      f"build={t_build - t0:.1f}s anim={t_anim - t_build:.1f}s export={t_end - t_anim:.1f}s")
