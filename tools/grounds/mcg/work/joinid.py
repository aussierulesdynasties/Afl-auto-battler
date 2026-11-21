# ID render of one join close-up: blender -b --python work/joinid.py -- <abs png> b z0 up
import sys, os, math, hashlib
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(SP, 'model'))
import bpy, mathutils, build
build.build_all(); sc = bpy.context.scene
names = {}
for m in list(bpy.data.materials):
    hh = hashlib.md5(m.name.encode()).digest(); col = (hh[0]/255, hh[1]/255, hh[2]/255, 1); names[m.name] = hh[:3].hex()
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = col
    o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0], o.inputs[0])
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.view_settings.view_transform = 'Standard'
cd = bpy.data.cameras.new('cam'); cd.lens_unit = 'FOV'; cd.angle = math.radians(55); cd.clip_end = 5000
co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
a = sys.argv[sys.argv.index('--') + 1:]; out = a[0]; b, z0, up = map(float, a[1:4])
dg = bpy.context.evaluated_depsgraph_get()
d = mathutils.Vector((-math.sin(math.radians(b)), -math.cos(math.radians(b)), 0)); o = mathutils.Vector((260*math.sin(math.radians(b)), 260*math.cos(math.radians(b)), z0))
ok, p, *_ = sc.ray_cast(dg, o, d); n = -d
eye = p + n*32 + mathutils.Vector((0, 0, 2)); t = p + mathutils.Vector((0, 0, up)); co.location = eye; co.rotation_euler = (t-eye).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
import json; json.dump(names, open(out + '.json', 'w'))
