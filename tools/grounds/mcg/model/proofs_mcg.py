# MCG proof renders + GLB. blender -b --python model/proofs_mcg.py -- out_dir [glb|stills|close|joins|orbit|ids ...]
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


def orbit(az, el=32, r=560):
    a, e = math.radians(az), math.radians(el)
    look((T.x + r * math.cos(e) * math.sin(a), T.y + r * math.cos(e) * math.cos(a), r * math.sin(e)), T)


def shot(path):
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print('rendered', path)


def facade_hit(b, z):
    """First surface met coming in from 260 m out along bearing b at height z."""
    d = mathutils.Vector((-math.sin(math.radians(b)), -math.cos(math.radians(b)), 0))
    o = mathutils.Vector((260 * math.sin(math.radians(b)), 260 * math.cos(math.radians(b)), z))
    ok, loc, nrm, *_ = sc.ray_cast(dg, o, d)
    return loc if ok else None


if 'glb' in jobs:
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'mcg.glb'), export_format='GLB',
                              use_selection=False, export_cameras=False, export_lights=False)
if 'stills' in jobs:
    for az in range(0, 360, 45):
        orbit(az); shot(os.path.join(out, f'turntable_{az:03d}.png'))
if 'close' in jobs:  # one sharp close-up per hand-painted facade texture, 18 m out at eye height 9 m
    cd.angle = math.radians(50)
    for b, name in ((3, 'north_entry'), (20, 'north_windows'), (31, 'north_open'), (50, 'ne_box'), (64, 'east_glass'),
                    (77.7, 'east_tower'), (80, 'east_glass2'), (95, 'east_precast'), (115.5, 'east_tower2'),
                    (135, 'se_block'), (145, 'se_porthole'), (159.5, 'south_balconies'), (163.5, 'south_recess'),
                    (183, 'south_gss'), (198.5, 'south_balconies2'), (224, 'sw_dark'), (242, 'sw_pale'),
                    (255.5, 'west_grey'), (265.5, 'mcc_windows'), (275, 'mcc_louvre'), (302, 'nw_recess'),
                    (314.5, 'nw_dark'), (334, 'nw_glass'), (344, 'nw_windows')):
        p = facade_hit(b, 9.0)
        if p is None: print('no hit', b); continue
        n = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0))
        look(p + n * 18 + mathutils.Vector((0, 0, 1.5)), p + mathutils.Vector((0, 0, 1.5)))
        shot(os.path.join(out, f'facade_{int(b):03d}_{name}.png'))
    cd.angle = math.radians(40)
if 'joins' in jobs:  # where parts meet: roof on facade, truss feet, screen on roof, light-tower foot, canopy
    cd.angle = math.radians(55)
    for b, z0, up, name in ((100, 18, 14, 'roof_facade_east'), (300, 18, 16, 'truss_feet_west'), (59, 20, 16, 'screen_ne'),
                            (242, 20, 16, 'screen_sw'), (5, 6, 10, 'north_canopy'), (180, 6, 18, 'south_gss'),
                            (172, 6, 14, 'gss_end'), (160, 6, 12, 'south_towers')):
        p = facade_hit(b, z0) or mathutils.Vector((150 * math.sin(math.radians(b)), 150 * math.cos(math.radians(b)), z0))
        n = mathutils.Vector((math.sin(math.radians(b)), math.cos(math.radians(b)), 0))
        look(p + n * 32 + mathutils.Vector((0, 0, 2)), p + mathutils.Vector((0, 0, up)))
        shot(os.path.join(out, f'join_{int(b):03d}_{name}.png'))
    cd.angle = math.radians(40)
if 'orbit' in jobs:
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    os.makedirs(os.path.join(out, 'orbit'), exist_ok=True)
    for k in range(120):
        orbit(k * 3); shot(os.path.join(out, 'orbit', f'f{k:03d}.png'))
