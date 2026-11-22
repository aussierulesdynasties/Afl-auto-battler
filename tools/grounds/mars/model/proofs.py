# Mars Stadium proof renders + GLB (same method as the MCG proofs). blender -b --python model/proofs.py -- out_dir [glb|stills|close|joins|seats|sign|orbit ...]
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
    for ob in sc.objects: ob.select_set(ob.type == 'MESH' and ob.name != 'seats')
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'mars.glb'), export_format='GLB',
                              use_selection=True, export_cameras=False, export_lights=False)
    C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.0]])          # Blender (x, y, z) -> glTF (x, z, -y)
    tm = build.MB('tmpl'); build.seat((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), 0.0, shell=tm)
    tri = [tm.V[f[k]] for f in tm.F for i in range(1, len(f) - 1) for k in (0, i, i + 1)]
    (np.array(tri) @ C.T).astype('<f4').tofile(os.path.join(out, 'seat_tmpl.bin'))
    xf = {}
    for P, t, o, z, col in build.SEAT_XF:   # one seats_<colour>.bin per seat colour (Oval3D.SEAT_COLOURS)
        A = np.array([[t[0], o[0], 0], [t[1], o[1], 0], [0, 0, 1.0]])
        xf.setdefault(col, []).append(np.hstack([C @ A @ C.T, (C @ np.array([P[0], P[1], z]))[:, None]]).ravel())
    for f in os.listdir(out):
        if f.startswith('seats_') and f.endswith('.bin'): os.remove(os.path.join(out, f))
    for col, X in xf.items(): np.array(X).astype('<f4').tofile(os.path.join(out, f'seats_{col}.bin'))
    print('seats instanced:', {k: len(v) for k, v in xf.items()}, 'template tris:', len(tri) // 3)
if 'ship' in jobs:   # later jobs film what ships: the exported GLB plus the seats rebuilt from the two .bin files
    import numpy as np
    C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.0]])
    for ob in [o for o in sc.objects if o.type == 'MESH']: bpy.data.objects.remove(ob)
    bpy.ops.import_scene.gltf(filepath=os.path.join(out, 'mars.glb'))
    T = np.fromfile(os.path.join(out, 'seat_tmpl.bin'), '<f4').reshape(-1, 3)
    me = None
    for f in sorted(os.listdir(out)):   # one mesh per seats_<colour>.bin, drawn in that texture's mean colour as the game does
        if not (f.startswith('seats_') and f.endswith('.bin')): continue
        col = f[6:-4]; X = np.fromfile(os.path.join(out, f), '<f4').reshape(-1, 3, 4)
        V = np.concatenate([T @ M[:, :3].T + M[:, 3] for M in X]) @ C
        me = bpy.data.meshes.new('seats_' + col); me.from_pydata([tuple(v) for v in V], [], [(i, i + 1, i + 2) for i in range(0, len(V), 3)])
        im = bpy.data.images.load(os.path.join(HERE, 'tex', col + '.png')); px = np.array(im.pixels[:]).reshape(-1, 4)
        sm = bpy.data.materials.new(col + '_mean'); sm.use_nodes = True
        c = px[:, :3].mean(0); c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)   # PNG pixels are sRGB
        sm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*c, 1)
        print('seat mean colour (linear):', col, c, 'srgb', px[:, :3].mean(0))
        me.materials.append(sm); me.update()
        import bmesh
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new('seats_' + col, me); sc.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
if 'stills' in jobs:
    for az in range(0, 360, 45):
        orbit(az); shot(os.path.join(out, f'turntable_{az:03d}.png'))
if 'close' in jobs:  # one close-up per hand-painted facade, 16 m out
    cd.angle = math.radians(50)
    for b, z, name in ((325, 5, 'nw_back'), (10, 5, 'north_back'), (51, 2.5, 'north_pavilion'), (69, 2.5, 'east_pavilion'), (120, 5, 'east_back'),
                       (175, 5, 'south_east_back'), (215, 5, 'sw_building'), (250, 6, 'gunns_back'), (295, 6, 'cw_back')):
        p = hit(b, z)
        if p is None: print('no hit', b); continue
        n = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0))
        look(p + n * 16 + mathutils.Vector((0, 0, 1.5)), p + mathutils.Vector((0, 0, 1.5)))
        shot(os.path.join(out, f'facade_{int(b):03d}_{name}.png'))
    cd.angle = math.radians(40)
if 'joins' in jobs:  # where parts meet, seen from outside 30 m out
    cd.angle = math.radians(55)
    for b, z0, up, name in ((305, 6, 8, 'cw_nw'), (280, 6, 8, 'gunns_cw'), (221, 5, 8, 'sw_gunns'), (208, 5, 6, 'es_sw'),
                            (40, 4, 6, 'north_ne_gap'), (60, 3, 9, 'scoreboard_base'), (76, 4, 6, 'ne_gap_east'), (157, 4, 5, 'south_tower_foot')):
        p = hit(b, z0) or mathutils.Vector((110 * math.sin(math.radians(b)), 110 * math.cos(math.radians(b)), z0))
        n = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0))
        look(p + n * 30 + mathutils.Vector((0, 0, 3)), p + mathutils.Vector((0, 0, up)))
        shot(os.path.join(out, f'join_{int(b):03d}_{name}.png'))
    cd.angle = math.radians(40)
if 'seats' in jobs:  # empty seats: from the boundary looking up into the Gunns and the Northern stand
    cd.angle = math.radians(45)
    for b, name in ((250, 'gunns'), (10, 'north'), (120, 'east')):
        s = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0)); p = s * (build.fence_r(b) - 6)
        look(p + mathutils.Vector((0, 0, 1.7)), p + s * 20 + mathutils.Vector((0, 0, 5)))
        shot(os.path.join(out, f'seats_{name}.png'))
    cd.angle = math.radians(40)
if 'boards' in jobs:   # both scoreboards, front and back, oblique so the gap to the NE tower shows
    import numpy as np
    cd.angle = math.radians(45); E = build.D['extras']
    B = E['board']; L, R = np.array(B['left']), np.array(B['right']); c = (L + R) / 2; u = (R - L) / np.linalg.norm(R - L)
    n = np.array([-u[1], u[0]]); n = n if np.dot(n, -c) > 0 else -n
    W = E['board_sw']; b = 0.5 * sum(W['b']); c2 = np.array(build.pol(b, W['r'])); n2 = -c2 / np.linalg.norm(c2)
    u2 = np.array([-n2[1], n2[0]])
    for name, cc, nn, uu, zc, d, side, h in (('ne_front', c, n, u, 9.2, 26, 9, 3.0), ('ne_back', c, -n, u, 9.2, 18, 9, 5.0),
                                             ('sw_front', c2, n2, u2, 13.0, 34, 8, 6.0), ('sw_back', c2, -n2, u2, 13.0, 24, 9, 8.0)):
        tg = mathutils.Vector((*cc, zc)); look(tg + mathutils.Vector((*(nn * d + uu * side), h - zc + 2)), tg)
        shot(os.path.join(out, f'board_{name}.png'))
    cd.angle = math.radians(40)
if 'seatcu' in jobs:   # empty seats from seat height: eye 1.2 m above a mid-rake tread, looking along the row
    cd.angle = math.radians(60)
    for b_, r_off, name in ((12, 9.0, 'north'), (245, 7.0, 'gunns')):
        b = min(build.AISLES, key=lambda a: abs(a - b_))   # stand in the aisle stair, eye 1.2 m above the tread
        s_ = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0)); t_ = mathutils.Vector((s_.y, -s_.x, 0))
        p = s_ * (build.fence_r(b) + r_off)
        ok, loc, *_ = sc.ray_cast(dg, p + mathutils.Vector((0, 0, 8.4)), mathutils.Vector((0, 0, -1)))
        z = (loc.z if ok else 4.0)
        eye = p + mathutils.Vector((0, 0, z + 1.2)); look(eye, eye + t_ * 10 - s_ * 2.5 + mathutils.Vector((0, 0, -1.6)))
        shot(os.path.join(out, f'seatcu_{name}.png'))
    cd.angle = math.radians(40)
if 'sign' in jobs:   # the name sign from the pitch, as in the photo
    cd.angle = math.radians(30)
    G = build.D['signs'][0]; c = mathutils.Vector((*G['c'], G['z0'] + G['h'] / 2))
    look(c + mathutils.Vector((24, -6, -6)), c); shot(os.path.join(out, 'sign_utas.png'))
    cd.angle = math.radians(40)
if 'orbit' in jobs:
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    os.makedirs(os.path.join(out, 'orbit'), exist_ok=True)
    for k in range(120):
        orbit(k * 3); shot(os.path.join(out, 'orbit', f'f{k:03d}.png'))
