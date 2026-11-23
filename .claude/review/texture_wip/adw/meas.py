import bpy,sys,math
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"orig.glb")
o=bpy.data.objects['stands'];me=o.data;mw=o.matrix_world;col=me.attributes['Color']
zs=[];rs=[];n=0;cs=[]
for p in me.polygons:
    if abs(p.normal.z)>0.2: continue
    c=mw@p.center; az=math.degrees(math.atan2(c.y,c.x)); r=math.hypot(c.x,c.y)
    if (p.normal.x*c.x+p.normal.y*c.y)>0 and r>90 and -115<az<-20 and c.z>8:
        n+=1; rs.append(r)
        for li in p.loop_indices: zs.append((mw@me.vertices[me.loops[li].vertex_index].co).z)
        cs.append(tuple(round(v,2) for v in col.data[p.loop_indices[0]].color[:3]))
import collections
print("N",n,"z",round(min(zs),1),round(max(zs),1),"r",round(min(rs)),round(max(rs)),collections.Counter(cs).most_common(4))
