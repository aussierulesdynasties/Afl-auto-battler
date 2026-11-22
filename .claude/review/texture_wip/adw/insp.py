import bpy,sys,math
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"orig.glb")
o=bpy.data.objects['stands'];me=o.data
print("ATTR",[(a.name,a.domain,a.data_type) for a in me.attributes],"UV",[u.name for u in me.uv_layers],"F",len(me.polygons))
m=o.material_slots[0].material
for n in m.node_tree.nodes: print("NODE",n.type,n.name,[ (i.name,getattr(i,'default_value',None) if not i.is_linked else 'L') for i in n.inputs][:3])
mw=o.matrix_world
# vertical faces, bin by azimuth and z
import collections
b=collections.defaultdict(float)
for p in me.polygons:
    nz=p.normal.z
    if abs(nz)>0.2: continue
    c=mw@p.center; az=round(math.degrees(math.atan2(c.y,c.x))/15)*15; r=math.hypot(c.x,c.y)
    out=(p.normal.x*c.x+p.normal.y*c.y)>0
    if out and r>90: b[(az,int(c.z//10)*10)]+=p.area
for k in sorted(b): 
    if b[k]>200: print("BIN",k,int(b[k]))
