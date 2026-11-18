"""Blender: import model/*.ply, render from the photo-matched camera (or an orbit camera).
args after --: MODE OUT [extra]   MODE = match | orbit ; orbit extra = angle_deg elev_deg dist"""
import bpy, json, math, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import shade
from mathutils import Matrix, Vector
argv = sys.argv[sys.argv.index('--') + 1:]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mode, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try: sc.render.engine = eng; break
    except Exception: pass

def mat_for(obj):
    m = bpy.data.materials.new(obj.name); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes.get('Principled BSDF')
    ca = nt.nodes.new('ShaderNodeVertexColor')
    if obj.data.color_attributes: ca.layer_name = obj.data.color_attributes[0].name
    nt.links.new(ca.outputs['Color'], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = 0.8
    obj.data.materials.append(m)

for f in sorted(glob.glob(os.path.join(ROOT, 'model', '*.ply'))):
    if os.environ.get('ONLY') and not any(k in os.path.basename(f) for k in os.environ['ONLY'].split(',')): continue
    bpy.ops.wm.ply_import(filepath=f)
    o = bpy.context.selected_objects[0]; shade.build(o)
    bpy.context.view_layer.objects.active = o
    try: bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception as e: print('smooth', e)

# light: low late-afternoon sun from the west-north-west (photo shadows), plus sky fill
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.0; sun.angle = 0.02
so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so)
az, el = math.radians(float(os.environ.get('SUN_AZ', '290'))), math.radians(float(os.environ.get('SUN_EL', '22')))
d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))  # direction toward sun (az from +x ccw)
so.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6

camd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', camd); sc.collection.objects.link(cam); sc.camera = cam
camd.clip_start = 1; camd.clip_end = 5000
c = json.load(open(os.path.join(ROOT, os.environ.get('CAM', 'cam.json'))))
p = c['p']; W, H = c.get('W', 1811), c.get('Himg', 1257)
if mode == 'match' and c.get('model') == 'cyl':
    # photo C: cylindrical panorama, verticals corrected (tools/fitC4.py). p = [x, y, yaw, f, cy], eye 1.6 m
    W, H = 3840, 2160; Cx, Cy, yaw, fo, cyy = p; sca = float(os.environ.get('RS', '1'))
    sc.render.resolution_x, sc.render.resolution_y = int(W * sca), int(H * sca)
    sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', '16')); sc.cycles.use_denoising = True
    f = Vector((math.cos(yaw), math.sin(yaw), 0)); r = Vector((math.sin(yaw), -math.cos(yaw), 0)); u = r.cross(f)
    cam.matrix_world = Matrix.Translation((Cx, Cy, 1.6)) @ Matrix((r, u, -f)).transposed().to_4x4()
    camd.type = 'PANO'; camd.panorama_type = 'CENTRAL_CYLINDRICAL'
    camd.central_cylindrical_range_u_min = -(W / 2) / fo; camd.central_cylindrical_range_u_max = (W / 2) / fo
    camd.central_cylindrical_range_v_min = (cyy - H) / fo; camd.central_cylindrical_range_v_max = cyy / fo
    sc.render.film_transparent = True
elif mode == 'top':  # straight down, orthographic: TOP='cx,cy,size' metres, square image of TRES px, north up
    tcx, tcy, tsz = map(float, os.environ.get('TOP', '0,-10,400').split(','))
    sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('TRES', '1600'))
    camd.type = 'ORTHO'; camd.ortho_scale = tsz; camd.clip_end = 2000
    cam.location = (tcx, tcy, 500.0); cam.rotation_euler = (0, 0, 0); sc.render.film_transparent = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.0, 0.0, 0.0, 1)
    if os.environ.get('LEAN'):  # shear like the off-nadir satellite: a point h m up shows (a*h, b*h) m away
        la, lb = map(float, os.environ['LEAN'].split(','))
        Sh = Matrix(((1, 0, la, 0), (0, 1, lb, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
        for ob in sc.objects:
            if ob.type == 'MESH': ob.matrix_world = Sh @ ob.matrix_world
elif mode == 'match':
    sc.render.resolution_x, sc.render.resolution_y = W, H
    Cx, Cy, Cz, yaw, pt, roll, fo, cx, cy = p
    cyw, syw, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pt), math.sin(pt), math.cos(roll), math.sin(roll)
    f = Vector((cyw * cp, syw * cp, sp)); r = Vector((syw, -cyw, 0)); u = r.cross(f)
    r2 = cr * r + sr * u; u2 = -sr * r + cr * u
    M = Matrix((r2, u2, -f)).transposed()
    cam.matrix_world = Matrix.Translation((Cx, Cy, Cz)) @ M.to_4x4()
    camd.sensor_fit = 'HORIZONTAL'; camd.sensor_width = 36.0; camd.lens = fo * 36.0 / W
    camd.shift_x = (W / 2 - cx) / W; camd.shift_y = (cy - H / 2) / W
    sc.render.film_transparent = True
else:
    ang, elev, dist = (0.0, 30.0, 420.0) if mode == 'turn' else (float(argv[2]), float(argv[3]), float(argv[4]))
    sc.render.resolution_x, sc.render.resolution_y = int(os.environ.get('RW', '1280')), int(os.environ.get('RH', '720'))
    a, e = math.radians(ang), math.radians(elev)
    pos = Vector((dist * math.cos(e) * math.cos(a), dist * math.cos(e) * math.sin(a), dist * math.sin(e)))
    tgt = Vector((0, -10, 12))
    if os.environ.get('POS'): pos = Vector(map(float, os.environ['POS'].split(','))) - (tgt := Vector(map(float, os.environ['TGT'].split(','))))
    cam.location = pos + tgt; cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    camd.lens = float(os.environ.get('LENS', '35'))
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.62, 0.72, 0.86, 1)
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'
if mode == 'turn':
    n = int(argv[2]); elev, dist = float(argv[3]), float(argv[4]); e = math.radians(elev); tgt = Vector((0, -10, 12))
    for i in range(n):
        a = 2 * math.pi * i / n + math.radians(135)
        cam.location = tgt + Vector((dist * math.cos(e) * math.cos(a), dist * math.cos(e) * math.sin(a), dist * math.sin(e)))
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, 'f%03d.png' % i); bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
