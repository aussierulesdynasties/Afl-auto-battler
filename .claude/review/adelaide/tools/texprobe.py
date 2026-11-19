"""Blender: measure the hand-made textures. Each big-surface material is put on a flat wall-like plane (UVs in metres,
v up), its base colour is rendered unlit (emission) straight on, at two sizes: 'far' 24 m across (game camera
distance) and 'near' 4 m across. tools/texstat.py then gives each one's grey-level stddev (0-255)."""
import bpy, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import shade
from mathutils import Matrix
argv = sys.argv[sys.argv.index('--') + 1:]; OUT = argv[0]
MATS = [('concrete_light', 2, (205, 200, 190)), ('concrete', 2, (184, 180, 170)), ('concrete_dark', 2, (70, 70, 72)),
        ('membrane', 3, (240, 236, 230)), ('steel_white', 4, (238, 238, 236)), ('steel_grey', 4, (170, 165, 160)),
        ('steel_dark', 4, (30, 30, 32)), ('fascia_cream', 0, (222, 210, 168)), ('paint_green', 0, (104, 132, 96)),
        ('seats_red', 1, (200, 62, 36)), ('seats_blue', 1, (35, 55, 77)), ('seats_grey', 1, (95, 105, 118)),
        ('hill_turf', 12, (96, 128, 58)), ('scoreboard', 13, (40, 52, 46)), ('copper', 10, (146, 121, 110)),
        ('brick', 6, (196, 138, 110)), ('glass', 5, (60, 80, 100))]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.use_denoising = False   # unlit emission: no noise
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0
cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 512
S = 24.0
for name, kind, col in MATS:
    for o in list(bpy.data.objects):
        if o.type == 'MESH': bpy.data.objects.remove(o)
    me = bpy.data.meshes.new(name)
    # a 24 m x 24 m vertical wall in the x-z plane facing -y, 48 x 48 quads so object-space noise varies
    n = 48; V = []; F = []; UV = []
    for j in range(n + 1):
        for i in range(n + 1): V.append((i * S / n, 0, j * S / n))
    for j in range(n):
        for i in range(n):
            a = j * (n + 1) + i; F.append((a, a + 1, a + n + 2, a + n + 1))
    me.from_pydata(V, [], F); me.update()
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'POINT')
    for k in range(len(V)): ca.data[k].color_srgb = (*(c / 255 for c in col), kind * 20 / 255)
    uv = me.uv_layers.new(name='UV')
    for poly in me.polygons:
        for li in poly.loop_indices:
            x, _, z = V[me.loops[li].vertex_index]; uv.data[li].uv = (x, z)
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); shade.build(o)
    nt = o.active_material.node_tree; bs = nt.nodes['Principled BSDF']
    src = bs.inputs['Base Color'].links[0].from_socket
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(src, em.inputs['Color'])
    nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    for tag, size in (('far', 24.0), ('near', 4.0)):
        cd.ortho_scale = size
        cam.matrix_world = Matrix.Translation((S / 2, -50, S / 2)) @ Matrix.Rotation(math.radians(90), 4, 'X')
        sc.render.filepath = os.path.join(OUT, f'{name}_{tag}.png'); bpy.ops.render.render(write_still=True)
