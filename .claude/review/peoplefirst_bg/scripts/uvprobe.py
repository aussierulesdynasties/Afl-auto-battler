import bpy, bmesh, numpy as np
o=bpy.data.objects['PeopleFirstStadium']; me=o.data
idx=[i for i,s in enumerate(o.material_slots) if s.material and s.material.name=='seats_up'][0]
uv=me.uv_layers.active.data; out=[]
for p in me.polygons:
    if p.material_index!=idx: continue
    us=np.array([uv[l].uv[:] for l in p.loop_indices]); out.append((p.area, us.min(0), us.max(0)))
    if len(out)>=2000: break
a=np.array([x[0] for x in out]); mn=np.array([x[1] for x in out]); mx=np.array([x[2] for x in out])
print('N',len(out),'area med',np.median(a),'uv span med',np.median(mx-mn,0),'uv min range',mn.min(0),mx.max(0))
print('NODES',[(n.type,getattr(n,'interpolation',None)) for n in o.material_slots[idx].material.node_tree.nodes])
