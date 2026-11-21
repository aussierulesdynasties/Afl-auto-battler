import bpy,bmesh,json,sys,numpy as np,math
D=sys.argv[-1]
J=json.load(open(D+'../obuild/geom.json'))
RF=np.array([p[:2] for p in J['roof']]);IN=np.array([p[:2] for p in J['inner']]);N=J['N'];K=J['K'];IZ=J['iz']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=D+'../obuild/hout/optus_stadium.glb')
o=bpy.data.objects['optus'];me=o.data
def mat(name,img):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(D+img);t.image.pack()
    nt.links.new(t.outputs[0],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=0.6;return m
me.materials.append(mat('roof_bay','roof_bay.png'));IB=len(me.materials)-1
me.materials.append(mat('roof_edge','roof_edge.png'));IE=len(me.materials)-1
iroof=[m.name for m in me.materials].index('roof');iwhite=[m.name for m in me.materials].index('white')
bm=bmesh.new();bm.from_mesh(me);uv=bm.loops.layers.uv.active;bm.faces.ensure_lookup_table()
d=IN-RF;L2=(d*d).sum(1)
def locate(x,y):
    q=np.array([x,y])-RF;t=np.clip((q*d).sum(1)/L2,0,1);e=((RF+d*t[:,None]-[x,y])**2).sum(1);i=int(e.argmin());return i,t[i],e[i]
nr=ne=0
for f in bm.faces:
    if f.material_index==iroof:
        idx=[];ts=[]
        for l in f.loops:
            i,t,_=locate(l.vert.co.x,l.vert.co.y);idx.append(i);ts.append(t)
        # unwrap across the seam at index 0
        if max(idx)-min(idx)>N/2: idx=[i+N if i<N/2 else i for i in idx]
        for l,i,t in zip(f.loops,idx,ts): l[uv].uv=(i/K,-round(t*30)/6)
        f.material_index=IB;nr+=1
    elif f.material_index==iwhite:
        c=f.calc_center_median()
        if IZ-1.3<c.z<IZ+0.5 and abs(f.normal.z)<0.3:
            i,t,e=locate(c.x,c.y)
            if t>0.97:
                for l in f.loops:
                    j,_,_=locate(l.vert.co.x,l.vert.co.y)
                    if abs(j-i)>N/2: j+= N if j<i else -N
                    a=math.atan2(l.vert.co.y-J['oc'][1],l.vert.co.x-J['oc'][0])
                    l[uv].uv=(j*((np.linalg.norm(d[i]) and 1)*0)+ (j/N)*2*math.pi*np.linalg.norm(IN[i]-J['oc'])/24.0,(l.vert.co.z-(IZ-1.0))/1.2)
                f.material_index=IE;ne+=1
bm.to_mesh(me);print('ROOF',nr,'EDGE',ne)
bpy.ops.export_scene.gltf(filepath=D+'optus_roof.glb',export_format='GLB')
