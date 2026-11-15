"""Export the vignette footballer (MPFB body, kit regions, our own jog and idle) as a rigged GLB.

blender --background --python export_player_glb.py -- BODY_TYPES.json TYPE OUT.glb
Same body, kit and poses the sprite sheets use (build_sprites.py), so the 3D oval copies the
director-passed motion rather than inventing one. One material per kit region (ARD_<region>),
so Godot recolours each club's guernsey, shorts and socks.
"""
import json, math, os, re, sys, time
import bpy

PIPE = os.environ.get("ARD_PIPELINE_BLENDER", os.path.join(os.path.dirname(__file__), "..", "..", "..", "ard-asset-pipeline", "tools", "blender"))
sys.path.insert(0, PIPE)
import ard_body
from poses import jog, idle, carry

t0 = time.time()
argv = sys.argv[sys.argv.index("--") + 1:]
presets, body_type, out = json.load(open(argv[0])), argv[1], argv[2]

bpy.ops.wm.read_homefile(use_empty=True)
# Real boots (director, 2026-11-15: "Real boots"): MakeHuman's low-cut sports shoe (shoes06),
# fitted and rigged with the body; its delete group takes the bare foot away under it. Joined
# into the body below as the boot region, so the club's boot colour draws it.
SHOE = os.environ.get("ARD_SHOE", "shoes06")
shoe_dir = os.path.join(ard_body.ASSETS_DIR, "clothes", SHOE)
# The shoe deletes the body to mid-shin and brings its own sock tube, whose top fights the
# body's sock in a jagged line. A copy of the asset deletes only the foot (base-mesh verts below
# ARD_SHOE_KEEP decimetres over the sole, inside the boot); the tube above the boot is cut off
# after the build, so the body's own sock runs down into the boot.
KEEP = float(os.environ.get("ARD_SHOE_KEEP", "0.9"))
if SHOE and KEEP > 0.0:
    import glob, shutil, tempfile
    base_obj = glob.glob(os.path.join(os.environ.get("APPDATA", ""), "Blender Foundation", "Blender", "5.2",
                                      "extensions", "**", "3dobjs", "base.obj"), recursive=True)[0]
    by = [float(l.split()[2]) for l in open(base_obj) if l.startswith("v ")]
    sole = min(by[:13380])
    tmp = os.path.join(tempfile.mkdtemp(), SHOE)
    shutil.copytree(shoe_dir, tmp)
    lines = open(os.path.join(tmp, SHOE + ".mhclo")).read().split(chr(10))
    i = lines.index("delete_verts")
    j = i + 1
    while j < len(lines) and re.match(r"^[0-9 -]+$", lines[j] or "x"):
        j += 1
    toks = " ".join(lines[i + 1:j]).split()
    ids, k = [], 0
    while k < len(toks):
        if k + 2 < len(toks) and toks[k + 1] == "-":
            ids += range(int(toks[k]), int(toks[k + 2]) + 1)
            k += 3
        else:
            ids.append(int(toks[k]))
            k += 1
    kept = [v for v in ids if by[v] - sole < KEEP]
    lines[i + 1:j] = [" ".join(str(v) for v in kept[n:n + 40]) for n in range(0, len(kept), 40)]
    open(os.path.join(tmp, SHOE + ".mhclo"), "w").write(chr(10).join(lines))
    print(f"SHOE DELETE {len(kept)} of {len(ids)} body verts (below {KEEP} dm)")
    shoe_dir = tmp
basemesh, rig = ard_body.build_body(body_type, presets[body_type]["macros"], targets=presets[body_type].get("targets"),
                                    extras=[shoe_dir] if SHOE else None)
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
uv1_name = uv1.name
col = me.color_attributes.new("kit", "FLOAT_COLOR", "CORNER")
# Not "kit_hair": that is already the hair field's attribute on the body, so Blender would name
# this layer "kit_hair.001" and a joined shoe's "kit_hair" would come in as a second, empty layer.
HAIR_UV = "uv_hair_front"
uv2 = me.uv_layers.new(name=HAIR_UV)
assert uv2.name == HAIR_UV, uv2.name
for li, loop in enumerate(me.loops):
    v = loop.vertex_index
    col.data[li].color = (g[v], sh[v], so[v], bo[v])
    uv1.data[li].uv = (gu[v], gv[v])
    uv2.data[li].uv = (ha[v], gf[v])
print(f"GUERNSEY u {min(gu):.2f}..{max(gu):.2f} v {min(gv):.2f}..{max(gv):.2f} front {min(gf):.2f}..{max(gf):.2f}")
me.color_attributes.active_color = col
me.color_attributes.render_color_index = me.color_attributes.find("kit")

# The boot itself (director, 2026-11-15: "boot is good"): a Tripo model made from his boot
# photos, kept in its own textured material (ARD_boot_real; the game leaves that surface out of
# the kit shader). MakeHuman's shoe stays only as the guide: each Tripo boot is scaled to the
# guide's length on that foot, turned to its toe line, stood on its sole, mirrored for the other
# foot, and takes the guide's rig weights (nearest face), so it moves exactly as the shoe did.
BOOT = os.environ.get("ARD_BOOT_GLB", os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")),
                                                     "Desktop", "footy assets", "boots", "tripo_boot.glb"))
BOOT_TRIS = int(os.environ.get("ARD_BOOT_TRIS", "1500"))   # per boot
BOOT_TEX = int(os.environ.get("ARD_BOOT_TEX", "512"))      # colour map size, pixels


def tripo_boots(guide, path, uv_name):
    from mathutils import Matrix, Vector
    before = set(bpy.data.objects)
    # Merged: glTF splits a vertex at every UV seam, and the decimate never collapses across them.
    bpy.ops.import_scene.gltf(filepath=path, merge_vertices=True)
    new = [o for o in bpy.data.objects if o not in before]
    src = next(o for o in new if o.type == "MESH")
    mw = src.matrix_world.copy()
    src.parent = None
    src.data.transform(mw)
    src.matrix_world = Matrix()
    for o in new:
        if o is not src:
            bpy.data.objects.remove(o)
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)   # the import leaves ~7k split
    bm.to_mesh(src.data)
    bm.free()
    n = sum(len(p.vertices) - 2 for p in src.data.polygons)
    dec = src.modifiers.new("decimate", "DECIMATE")
    dec.ratio = min(1.0, BOOT_TRIS / n)
    low = bpy.data.meshes.new_from_object(src.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    src.modifiers.clear()
    src.data = low
    # Colour map only: the metal-rough and normal maps add megabytes a 2 cm boot on a phone can't show.
    mat = low.materials[0]
    mat.name = "ARD_boot_real"
    nt = mat.node_tree
    bsdf = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    base = bsdf.inputs["Base Color"].links[0].from_node
    for nd in list(nt.nodes):
        if nd not in (bsdf, base) and nd.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(nd)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.6
    if base.image.size[0] > BOOT_TEX:
        base.image.scale(BOOT_TEX, BOOT_TEX)
    low.uv_layers[0].name = uv_name

    def box(vs):
        return (Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))),
                Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs))))

    sv = [v.co.copy() for v in low.vertices]
    lo, hi = box(sv)
    length0 = hi.y - lo.y
    mid0 = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    # The toe is at -Y (the body faces -Y). Its tip leans toward the big toe: + means toward +X.
    tip = [v for v in sv if v.y < lo.y + 0.05 * length0]
    lean = sum(v.x for v in tip) / len(tip) - mid0.x
    gw = [guide.matrix_world @ v.co for v in guide.data.vertices]
    made = []
    for side in (-1, 1):        # -1 = his right foot (facing -Y, his right is -X)
        g = [w for w in gw if w.x * side > 0.0]
        cx, cy = sum(w.x for w in g) / len(g), sum(w.y for w in g) / len(g)
        sxx = sum((w.x - cx) ** 2 for w in g)
        syy = sum((w.y - cy) ** 2 for w in g)
        sxy = sum((w.x - cx) * (w.y - cy) for w in g)
        ang = 0.5 * math.atan2(2 * sxy, sxx - syy)          # the guide's long axis, from +X
        ax = Vector((math.cos(ang), math.sin(ang), 0.0))
        if ax.y > 0:
            ax = -ax                                           # point it at the toe (-Y)
        yaw = math.atan2(ax.y, ax.x) + math.pi / 2             # turn from the boot's -Y to the axis
        proj = [(w.x - cx) * ax.x + (w.y - cy) * ax.y for w in g]
        length = max(proj) - min(proj)
        c = Vector((cx, cy, 0.0)) + ax * ((max(proj) + min(proj)) / 2)
        c.z = min(w.z for w in g)
        s = length / length0
        # Big toe toward the body's middle: +X on his right foot, -X on his left.
        mx = 1.0 if lean * -side > 0 else -1.0
        m = (Matrix.Translation(c) @ Matrix.Rotation(yaw, 4, "Z")
             @ Matrix.Diagonal((mx * s, s, s, 1.0)) @ Matrix.Translation(-mid0))
        me2 = low.copy()
        me2.transform(m)
        if mx < 0:
            me2.flip_normals()
        ob2 = bpy.data.objects.new(f"boot_{'r' if side < 0 else 'l'}", me2)
        bpy.context.scene.collection.objects.link(ob2)
        for vg in guide.vertex_groups:
            ob2.vertex_groups.new(name=vg.name)
        dt = ob2.modifiers.new("weights", "DATA_TRANSFER")
        dt.object = guide
        dt.use_vert_data = True
        dt.data_types_verts = {"VGROUP_WEIGHTS"}
        dt.vert_mapping = "POLYINTERP_NEAREST"
        dt.layers_vgroup_select_src = "ALL"
        dt.layers_vgroup_select_dst = "NAME"
        with bpy.context.temp_override(object=ob2, active_object=ob2, selected_objects=[ob2]):
            bpy.ops.object.modifier_apply(modifier=dt.name)
        # White: Godot's glTF import multiplies every material in this mesh by its vertex colour,
        # and the boot keeps its own material (never the kit shader), so the colour must not tint it.
        kc = me2.color_attributes.new("kit", "FLOAT_COLOR", "CORNER")
        for li in range(len(me2.loops)):
            kc.data[li].color = (1.0, 1.0, 1.0, 1.0)
        me2.uv_layers.new(name=HAIR_UV)
        for d in me2.uv_layers[HAIR_UV].data:
            d.uv = (0.0, 0.0)
        print(f"BOOT {ob2.name}: length {length:.3f} m, scale {s:.3f}, yaw {math.degrees(yaw):.1f} deg, "
              f"mirror {mx < 0}, sole z {c.z:.3f}, tris {sum(len(p.vertices) - 2 for p in me2.polygons)}")
        made.append(ob2)
    print(f"BOOT source {n} tris, toe lean {lean:+.4f}, texture {tuple(base.image.size)}")
    bpy.data.objects.remove(src)
    bpy.data.objects.remove(guide)
    bpy.ops.object.select_all(action="DESELECT")
    for o in made:
        o.select_set(True)
    bpy.context.view_layer.objects.active = made[0]
    bpy.ops.object.join()
    return made[0]


# The shoe: boot weight (colour alpha) below the ankle, no guernsey coordinates, no hair; same
# layer names as the body so the join merges them; then joined into the body mesh.
shoe_tris = 0
for name in json.loads(basemesh.get("extras", "[]")):
    ob = bpy.data.objects[name]
    sm = ob.data
    while sm.uv_layers:
        sm.uv_layers.remove(sm.uv_layers[0])
    su1 = sm.uv_layers.new(name=uv1.name)
    su2 = sm.uv_layers.new(name=HAIR_UV)
    scol = sm.color_attributes.new("kit", "FLOAT_COLOR", "CORNER")
    # The shoe asset carries its own sock up the shin: above the ankle it is the sock (the kit's
    # own rule, ard_body: sock above ankle + 3 cm), with the sock band's coordinates; a 1 cm
    # ramp puts the boot's top edge on a level line rather than along the faces.
    collar = sum(ard_body._head(rig, f"foot_{x}").z for x in "lr") / 2 + 0.03
    zs = [(ob.matrix_world @ v.co).z for v in sm.vertices]
    for li, loop in enumerate(sm.loops):
        z = zs[loop.vertex_index]
        k = min(1.0, max(0.0, (z - collar) / 0.01 + 0.5))
        scol.data[li].color = (0.0, 0.0, k, 1.0 - k)
        su1.data[li].uv = (0.0, (z - (knee_z - 0.17)) / 0.06 if k > 0.0 else 0.0)
        su2.data[li].uv = (0.0, 0.0)
    # The shoe's own sock tube above the boot is cut off on a level line: the body's sock
    # (kept down into the boot, see KEEP) is the sock there.
    TRIM = float(os.environ.get("ARD_SHOE_TRIM", "-0.008"))   # under the colour line: the cut edge is all boot
    if KEEP > 0.0:
        import bmesh
        from mathutils import Vector
        bm = bmesh.new()
        bm.from_mesh(sm)
        inv = ob.matrix_world.inverted()
        co = inv @ Vector((0.0, 0.0, collar + TRIM))
        no = (inv.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no,
                               clear_outer=True)
        bm.to_mesh(sm)
        bm.free()
    # The body's ankle under the collar is tucked in toward the leg's middle (TUCK metres), so the
    # sock never shows outside the boot's rim at the heel.
    TUCK = float(os.environ.get("ARD_SHOE_TUCK", "0.006"))
    if KEEP > 0.0 and TUCK > 0.0:
        bw = basemesh.matrix_world
        biw = bw.inverted()
        low = [v for v in basemesh.data.vertices if (bw @ v.co).z < collar + 0.01]
        for side in (-1, 1):
            vs = [v for v in low if (bw @ v.co).x * side > 0.0]
            if not vs:
                continue
            for v in vs:
                w = bw @ v.co
                ring = [bw @ u.co for u in vs if abs((bw @ u.co).z - w.z) < 0.005]
                mid = sum(ring, Vector()) / len(ring)
                d = Vector((w.x - mid.x, w.y - mid.y, 0.0))
                if d.length > TUCK * 2:
                    v.co = biw @ (w - d.normalized() * TUCK * min(1.0, (collar + 0.01 - w.z) / 0.01))
    body_z = [(basemesh.matrix_world @ v.co).z for v in basemesh.data.vertices]
    print(f"SHOE CUT at {collar + TRIM:.3f}; lowest body z {min(body_z):.3f}, collar {collar:.3f}")
    if BOOT and os.path.exists(BOOT):
        ob = tripo_boots(ob, BOOT, uv1.name)
        sm = ob.data
    else:
        sm.materials.clear()
        sm.materials.append(bpy.data.materials.get("ARD_boot"))
    shoe_tris += sum(len(p.vertices) - 2 for p in sm.polygons)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    basemesh.select_set(True)
    bpy.context.view_layer.objects.active = basemesh
    bpy.ops.object.join()
    me = basemesh.data
if shoe_tris:
    bpy.ops.object.vertex_group_limit_total(group_select_mode="BONE_DEFORM", limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode="BONE_DEFORM", lock_active=False)
    print(f"BOOTS {SHOE}: {shoe_tris} tris joined")
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

# Godot reads glTF TEXCOORD_0 as UV and TEXCOORD_1 as UV2, and the kit shader needs exactly
# [guernsey coordinates, hair/front] there: a third layer pushes hair/front to TEXCOORD_2, where
# Godot never reads it, so the design and the number lose front and back (#1606's shoe join did
# this: no chevrons, the back number through the chest).
uvs = basemesh.data.uv_layers
print("UV layers before export:", [l.name for l in uvs])
assert [l.name for l in uvs] == [uv1_name, HAIR_UV], [l.name for l in uvs]

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
