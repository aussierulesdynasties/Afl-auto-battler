import bpy,sys,math
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"gmhba_tex.glb")
o=[x for x in bpy.data.objects if x.type=='MESH'][0];me=o.data;uv=me.uv_layers.active.data
idx=[i for i,s in enumerate(o.material_slots) if s.material and s.material.name=='wall'][0]
fs=[p for p in me.polygons if p.material_index==idx];print("faces",len(fs),"area",sum(p.area for p in fs))
import random;random.seed(1)
for p in random.sample(fs,12):
    for li in list(p.loop_indices)[:3]:
        v=o.matrix_world@me.vertices[me.loops[li].vertex_index].co
        print("P%d"%p.index,"az%.1f r%.1f z%.1f"%(math.degrees(math.atan2(v.y,v.x)),math.hypot(v.x,v.y),v.z),"uv%.3f,%.3f"%tuple(uv[li].uv),"n%.2f,%.2f,%.2f"%tuple(p.normal))
zs=[(o.matrix_world@me.vertices[i].co).z for p in fs for i in p.vertices];print("zrange",min(zs),max(zs))
