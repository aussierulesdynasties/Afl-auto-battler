"""The injury clips (retarget_mixamo.py's .blend) as assets/oval3d/injury_clips.glb: the
footballer's rig and its actions only, no mesh (Oval3DInjury puts them on each figure's own
skeleton by bone name, as Oval3D._loop_anims does with the loops).

  python bake_injury_glb.py -- CLIPS.blend[,MORE.blend ...] OUT.glb NAME [NAME ...]

Clips retargeted in later runs (MORE.blend) join the first file's rig as NLA tracks of their own.
"""
import sys
import os
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
blends, out, keep = argv[0].split(","), argv[1], set(argv[2:])
bpy.ops.wm.open_mainfile(filepath=blends[0])
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
for more in blends[1:]:
    with bpy.data.libraries.load(more, link=False) as (src, dst):
        dst.actions = [a for a in src.actions if a in keep]
    for a in dst.actions:
        if a.name in rig.animation_data.nla_tracks:
            raise SystemExit(f"clip {a.name} in two files")
        tr = rig.animation_data.nla_tracks.new()
        tr.name = a.name
        tr.strips.new(a.name, int(a.frame_range[0]), a)
for o in list(bpy.data.objects):
    if o != rig:
        bpy.data.objects.remove(o, do_unlink=True)
for tr in list(rig.animation_data.nla_tracks):
    if tr.name not in keep:
        rig.animation_data.nla_tracks.remove(tr)
for tr in rig.animation_data.nla_tracks:
    tr.mute = False
lost = keep - {tr.name for tr in rig.animation_data.nla_tracks}
if lost:
    raise SystemExit(f"missing clips {sorted(lost)}")
rig.animation_data.action = None
# Keys a second: the first .blend's own (retarget_bvh.py saves its GAIT_FPS there). BAKE_FPS, when given,
# must agree, so a clip keyed at 60 (the sprint) never bakes at 30 and plays at half speed. Blender's
# untouched default (24) means nobody set it: say which with BAKE_FPS.
blend_fps = bpy.context.scene.render.fps
want = os.environ.get("BAKE_FPS", "")
if want and int(want) != blend_fps:
    raise SystemExit(f"BAKE_FPS={want} but {blends[0]} is keyed at {blend_fps} fps: the clip would play at the wrong speed")
if not want and blend_fps == 24:
    raise SystemExit(f"{blends[0]} is at Blender's default 24 fps: pass BAKE_FPS (30 for the injury clips)")
bpy.context.scene.render.fps = int(want) if want else blend_fps
print(f"BAKE at {bpy.context.scene.render.fps} fps")
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_animations=True,
                          export_animation_mode="NLA_TRACKS", export_skins=True,
                          export_force_sampling=True, export_frame_step=1, export_optimize_animation_size=True,
                          export_anim_single_armature=True, export_reset_pose_bones=True)
print("BAKED", out, sorted(keep))
