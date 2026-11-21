# Proofs and the GLB for a ground built by kit/build.py.
# GROUND=tools/grounds/<slug> blender -b --python tools/grounds/kit/proofs.py -- out_dir [glb] [ship] [stills] [top] [seats] [low] [orbit]
# glb: <slug>.glb plus seat_tmpl.bin and seats_<colour>.bin (the format Oval3D._ground_model reads), written to out_dir.
# ship: later jobs film what ships (the exported GLB and the seats rebuilt from the .bin files, each flat in its mean colour).
# top: straight-down orthographic render matching work/sat.png (0.25 m/px, +-HALF m, north up).
import sys, os, math, glob
KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT)
import bpy, mathutils
import numpy as np
import build
GROUND, SLUG, D = build.GROUND, build.SLUG, build.D
build.build_all()
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng; break
    except Exception:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.render.resolution_percentage = 100
try:
    sc.eevee.taa_render_samples = int(os.environ.get('SAMPLES', 8))   # software GL in the cloud: few samples keep a still under 10 s
except Exception:
    pass
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.68, 0.85, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.2; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
north = D.get('lat', -30) < 0   # sun in the north for the southern hemisphere
so.rotation_euler = (math.radians(35), 0, math.radians(200 if north else 20))
cd = bpy.data.cameras.new('cam'); cd.lens_unit = 'FOV'; cd.angle = math.radians(40); cd.clip_end = 5000
co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
argv = sys.argv[sys.argv.index('--') + 1:]; out = os.path.abspath(argv[0]); jobs = argv[1:]
os.makedirs(out, exist_ok=True)
T = mathutils.Vector((0, 0, 5))
C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.0]])   # Blender (x, y, z) -> glTF (x, z, -y)


def look(eye, tgt):
    eye = mathutils.Vector(eye); d = mathutils.Vector(tgt) - eye
    co.location = eye; co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def orbit(az, el=32, r=380):
    a, e = math.radians(az), math.radians(el)
    look((T.x + r * math.cos(e) * math.sin(a), T.y + r * math.cos(e) * math.cos(a), r * math.sin(e)), T)


def shot(path):
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print('rendered', path)


if 'glb' in jobs:
    for ob in sc.objects: ob.select_set(ob.type == 'MESH' and ob.name != 'seats')
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, SLUG + '.glb'), export_format='GLB',
                              use_selection=True, export_cameras=False, export_lights=False)
    tm = build.MB('tmpl'); build.seat((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), 0.0, shell=tm)
    tri = [tm.V[f[k]] for f in tm.F for i in range(1, len(f) - 1) for k in (0, i, i + 1)]
    (np.array(tri) @ C.T).astype('<f4').tofile(os.path.join(out, 'seat_tmpl.bin'))
    for f in glob.glob(os.path.join(out, 'seats_*.bin')): os.remove(f)
    xf = {}
    for P, t, o, z, col in build.SEAT_XF:
        A = np.array([[t[0], o[0], 0], [t[1], o[1], 0], [0, 0, 1.0]])
        xf.setdefault(col, []).append(np.hstack([C @ A @ C.T, (C @ np.array([P[0], P[1], z]))[:, None]]).ravel())
    for col, L in xf.items(): np.array(L).astype('<f4').tofile(os.path.join(out, f'seats_{col}.bin'))
    print('seats instanced:', {k: len(v) for k, v in xf.items()}, 'total', sum(len(v) for v in xf.values()))
if 'ship' in jobs:
    import bmesh
    for ob in [o for o in sc.objects if o.type == 'MESH']: bpy.data.objects.remove(ob)
    bpy.ops.import_scene.gltf(filepath=os.path.join(out, SLUG + '.glb'))
    TM = np.fromfile(os.path.join(out, 'seat_tmpl.bin'), '<f4').reshape(-1, 3)
    for fb in sorted(glob.glob(os.path.join(out, 'seats_*.bin'))):
        col = os.path.basename(fb)[6:-4]
        X = np.fromfile(fb, '<f4').reshape(-1, 3, 4)
        V = np.concatenate([TM @ M[:, :3].T + M[:, 3] for M in X]) @ C
        me = bpy.data.meshes.new('seats_' + col); me.from_pydata([tuple(v) for v in V], [], [(i, i + 1, i + 2) for i in range(0, len(V), 3)])
        im = bpy.data.images.load(os.path.join(build.HERE, 'tex', col + '.png')); px = np.array(im.pixels[:]).reshape(-1, 4)
        sm = bpy.data.materials.new('mean_' + col); sm.use_nodes = True
        c = px[:, :3].mean(0); c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        sm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*c, 1)
        print('seat mean colour (sRGB):', col, [round(float(v), 3) for v in px[:, :3].mean(0)])
        me.materials.append(sm); me.update()
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new('seats_' + col, me); sc.collection.objects.link(ob)
if 'stills' in jobs:
    for az in range(0, 360, 45):
        orbit(az); shot(os.path.join(out, f'turntable_{az:03d}.png'))
if 'low' in jobs:   # from the boundary, 1.7 m up, looking out at each quarter of the ground
    cd.angle = math.radians(60)
    for b in range(0, 360, 45):
        s = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0)); p = s * (build.fence_r(b) - 12)
        look(p + mathutils.Vector((0, 0, 1.7)), p + s * 40 + mathutils.Vector((0, 0, 6)))
        shot(os.path.join(out, f'low_{b:03d}.png'))
    cd.angle = math.radians(40)
if 'seats' in jobs:   # empty seats close: from the front of each seated stand
    cd.angle = math.radians(50)
    for S in D['stands']:
        if S['kind'] == 'bank' or S.get('no_seats'): continue
        if S['kind'] == 'straight':   # stand square-on from the field, 14 m in front of its front edge
            A, B = np.array(S['a'], float), np.array(S['b'], float); u = (B - A) / np.linalg.norm(B - A); n = np.array([u[1], -u[0]])
            c2 = (A + B) / 2
            if n @ c2 < 0: n = -n
            p = mathutils.Vector((*(c2 - n * 14), 2.0)); q = mathutils.Vector((*(c2 + n * S['depth'] / 2), S['z_seat'][1] / 2 + 1))
            look(p, q); shot(os.path.join(out, f'seats_{S["name"]}.png')); continue
        else:
            b = 0.5 * (S['b0'] + S['b1'])
        s = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0))
        p = s * (build.fence_r(b % 360) - 6)
        look(p + mathutils.Vector((0, 0, 2.0)), p + s * 22 + mathutils.Vector((0, 0, 5)))
        shot(os.path.join(out, f'seats_{S["name"]}.png'))
    cd.angle = math.radians(40)
if 'top' in jobs:
    H = D.get('half', 260)
    sc.render.resolution_x = sc.render.resolution_y = int(4 * 2 * H); sc.render.film_transparent = True
    cd.type = 'ORTHO'; cd.ortho_scale = 2.0 * H; co.location = (0, 0, 500); co.rotation_euler = (0, 0, 0)
    shot(os.path.join(out, 'top.png')); sc.render.film_transparent = False; cd.type = 'PERSP'
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
if 'orbit' in jobs:
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    os.makedirs(os.path.join(out, 'orbit'), exist_ok=True)
    nf = int(os.environ.get('ORBIT_FRAMES', 48))
    for k in range(nf):
        orbit(k * 360 / nf); shot(os.path.join(out, 'orbit', f'f{k:03d}.png'))
