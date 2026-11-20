# Cazaly's Stadium proof renders + GLB (same method as the MCG proofs). blender -b --python model/proofs.py -- out_dir [glb|stills|close|joins|seats|sign|orbit ...]
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(SP, 'work'))
import bpy, mathutils
import build
build.build_all()
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng; break
    except Exception:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.68, 0.85, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.2; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(35), 0, math.radians(200))
cd = bpy.data.cameras.new('cam'); cd.lens_unit = 'FOV'; cd.angle = math.radians(40); cd.clip_end = 5000
co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
argv = sys.argv[sys.argv.index('--') + 1:]; out = argv[0]; jobs = argv[1:]
os.makedirs(out, exist_ok=True)
T = mathutils.Vector((0, 0, 5))
dg = bpy.context.evaluated_depsgraph_get()


def look(eye, tgt):
    eye = mathutils.Vector(eye); d = mathutils.Vector(tgt) - eye
    co.location = eye; co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def orbit(az, el=32, r=380):
    a, e = math.radians(az), math.radians(el)
    look((T.x + r * math.cos(e) * math.sin(a), T.y + r * math.cos(e) * math.cos(a), r * math.sin(e)), T)


def shot(path):
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print('rendered', path)


def hit(b, z, inward=True):
    """first surface met along bearing b at height z: from 200 m out coming in, or from the centre going out"""
    s = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0))
    o, d = (s * 200 + mathutils.Vector((0, 0, z)), -s) if inward else (mathutils.Vector((0, 0, z)), s)
    ok, loc, nrm, *_ = sc.ray_cast(dg, o, d)
    return loc if ok else None


if 'glb' in jobs:   # Blender +Y (north) becomes glTF -Z
    # the seat shells stay out of the GLB: one shell (seat_tmpl.bin, triangles, glTF frame) drawn once per seat
    # from seats_seat_plastic.bin (row-major 3x4 per seat), the MCG format Oval3D._ground_model reads
    import numpy as np
    for ob in sc.objects: ob.select_set(ob.type == 'MESH' and not ob.name.startswith('seats_'))
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'cazalys.glb'), export_format='GLB',
                              use_selection=True, export_cameras=False, export_lights=False)
    C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.0]])          # Blender (x, y, z) -> glTF (x, z, -y)
    tm = build.MB('tmpl'); build.seat((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), 0.0, 'seat', shell=tm)
    tri = [tm.V[f[k]] for f in tm.F for i in range(1, len(f) - 1) for k in (0, i, i + 1)]
    (np.array(tri) @ C.T).astype('<f4').tofile(os.path.join(out, 'seat_tmpl.bin'))
    xf = {}
    for P, t, o, z, col in build.SEAT_XF:
        A = np.array([[t[0], o[0], 0], [t[1], o[1], 0], [0, 0, 1.0]])
        xf.setdefault(col, []).append(np.hstack([C @ A @ C.T, (C @ np.array([P[0], P[1], z]))[:, None]]).ravel())
    for col, L in xf.items():
        np.array(L).astype('<f4').tofile(os.path.join(out, f'seats_{col}.bin')); print('seats', col, len(L))
    print('seats instanced:', sum(map(len, xf.values())), 'template tris:', len(tri) // 3)
if 'ship' in jobs:   # later jobs film what ships: the exported GLB plus the seats rebuilt from the two .bin files
    import numpy as np
    C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.0]])
    for ob in [o for o in sc.objects if o.type == 'MESH']: bpy.data.objects.remove(ob)
    bpy.ops.import_scene.gltf(filepath=os.path.join(out, 'cazalys.glb'))
    TT = np.fromfile(os.path.join(out, 'seat_tmpl.bin'), '<f4').reshape(-1, 3)
    import bmesh, glob
    for fp in glob.glob(os.path.join(out, 'seats_*.bin')):
        col = os.path.basename(fp)[6:-4]
        X = np.fromfile(fp, '<f4').reshape(-1, 3, 4)
        V = np.concatenate([TT @ M[:, :3].T + M[:, 3] for M in X]) @ C
        me = bpy.data.meshes.new('inst_' + col); me.from_pydata([tuple(v) for v in V], [], [(i, i + 1, i + 2) for i in range(0, len(V), 3)])
        im = bpy.data.images.load(os.path.join(HERE, 'tex', col + '.png')); px = np.array(im.pixels[:]).reshape(-1, 4)
        sm = bpy.data.materials.new('mean_' + col); sm.use_nodes = True   # the game draws seats in one colour: the texture mean
        c = px[:, :3].mean(0); c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        sm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*c, 1)
        print('seat mean colour (linear):', col, c)
        me.materials.append(sm); me.update()
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new('inst_' + col, me); sc.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
if 'stills' in jobs:
    for az in range(0, 360, 45):
        orbit(az); shot(os.path.join(out, f'turntable_{az:03d}.png'))
def at(x, y, z): return mathutils.Vector((x, y, z))


def pv(b, r, z): return at(r * math.sin(math.radians(b)), r * math.cos(math.radians(b)), z)


if 'close' in jobs:  # one close-up per hand-painted facade: (name, eye, target, fov)
    for name, e, t, f in (('grandstand_rear', pv(238, 150, 6), pv(238, 110, 8), 50), ('grandstand_front', pv(238, 50, 3), pv(238, 95, 9), 60),
                          ('club_front', at(0, -70, 3), at(0, -100, 5), 60), ('bldg_w', at(-150, -55, 3), at(-112, -12, 4), 55),
                          ('shelters', at(-55, 40, 2), at(-72, 52, 1.5), 60), ('bleacher', at(-30, 55, 2), at(-45, 75, 2.5), 60),
                          ('nw_tents', at(-118, 52, 2), at(-80, 45, 3), 60), ('north_marquee', at(10, 82, 2), at(7.5, 101, 3), 60),
                          ('east_marquee', at(80, 2, 2), at(99, 2.5, 3), 60), ('coach_box', at(64, -58, 1.6), at(70, -65.6, 1.3), 50),
                          ('club_sails', at(5, -75, 2), at(5, -92, 3.5), 70)):
        cd.angle = math.radians(f); look(e, t); shot(os.path.join(out, f'facade_{name}.png'))
    cd.angle = math.radians(40)
if 'joins' in jobs:  # where parts meet
    cd.angle = math.radians(55)
    for name, e, t in (('gs_south_end', pv(222, 60, 6), pv(226, 95, 6)), ('gs_north_end', pv(256, 60, 6), pv(252, 95, 6)),
                       ('gs_rear_south', pv(220, 135, 5), pv(226, 112, 7)), ('gs_rear_north', pv(258, 128, 5), pv(252, 106, 7)),
                       ('terrace_s_end', pv(198, 70, 3), pv(202, 90, 2)), ('terrace_n_end', pv(285, 70, 3), pv(281, 88, 2)),
                       ('roof_masts', pv(238, 55, 22), pv(238, 92, 17)), ('club_corner', at(75, -60, 4), at(37, -94, 4))):
        look(e, t); shot(os.path.join(out, f'join_{name}.png'))
    cd.angle = math.radians(40)
if 'seats' in jobs:  # empty seats from the boundary looking up into the stands, and from below
    cd.angle = math.radians(50)
    for b, name in ((239, 'grandstand'), (212, 'terrace_south'), (266, 'terrace_north'), (45, 'boundary_ne'), (140, 'boundary_se')):
        s_ = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0)); p = s_ * (build.fence_r(b) - 5)
        look(p + mathutils.Vector((0, 0, 1.0)), p + s_ * 18 + mathutils.Vector((0, 0, 4 if b > 200 else 0.5)))
        shot(os.path.join(out, f'seats_{name}.png'))
    cd.angle = math.radians(40)
if 'seatcu' in jobs:   # empty seats from seat height: eye 1.2 m above a tread in the aisle, looking along the row
    cd.angle = math.radians(60)
    for b_, r_off, z_top, name in ((236, 4.0, 6.0, 'grandstand_lower'), (236, 14.0, 12.0, 'grandstand_upper'), (268, 4.0, 6.0, 'terrace_north')):
        b = min(build.AISLES, key=lambda a: abs(a - b_))
        s_ = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0)); t_ = mathutils.Vector((s_.y, -s_.x, 0))
        p = s_ * (build.fence_r(b) + r_off)
        ok, loc, *_ = sc.ray_cast(dg, p + mathutils.Vector((0, 0, z_top)), mathutils.Vector((0, 0, -1)))
        z = (loc.z if ok else 2.0)
        eye = p + mathutils.Vector((0, 0, z + 1.2)); look(eye, eye + t_ * 10 - s_ * 2.5 + mathutils.Vector((0, 0, -1.6)))
        shot(os.path.join(out, f'seatcu_{name}.png'))
    cd.angle = math.radians(40)
if 'sign' in jobs:   # each name sign as in its photo
    for name, e, t, f in (('scoreboard', at(19, 44, 1.6), at(26, 86, 6.5), 42), ('scoreboard_top', at(23, 70, 3), at(26.1, 86.4, 11.8), 28),
                          ('gate', at(-12, 152, 1.6), at(-10, 128, 3), 40), ('hopgood', at(3, 142, 1.5), at(1.5, 135.4, 1.3), 45)):
        cd.angle = math.radians(f); look(e, t); shot(os.path.join(out, f'sign_{name}.png'))
    cd.angle = math.radians(40)
if 'orbit' in jobs:
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    os.makedirs(os.path.join(out, 'orbit'), exist_ok=True)
    for k in range(120):
        orbit(k * 3); shot(os.path.join(out, 'orbit', f'f{k:03d}.png'))
