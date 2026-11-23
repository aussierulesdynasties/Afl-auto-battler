import bpy,bmesh,json,sys,numpy as np
D=sys.argv[-1];J=json.load(open(D+'../obuild/geom.json'))
RF=np.array([p[:2] for p in J['roof']]);IN=np.array([p[:2] for p in J['inner']]);IZ=J['iz'];ZF=46.55
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof.glb')
o=bpy.data.objects['optus'];me=o.data;names=[m.name for m in me.materials]
ib=names.index('roof_bay');iw=names.index('white')
img=me.materials[ib].node_tree.nodes['Image Texture'].image;img.filepath=D+'roof_bay.png';img.unpack(method='REMOVE') if img.packed_file else None;img.reload();img.pack()
d=IN-RF;L2=(d*d).sum(1)
def loc(x,y):
    q=np.array([x,y])-RF;t=(q*d).sum(1)/L2;tc=np.clip(t,0,1);e=((RF+d*tc[:,None]-[x,y])**2).sum(1);i=int(e.argmin());return t[i],e[i]
bm=bmesh.new();bm.from_mesh(me)
vs=set(v for f in bm.faces if f.material_index==ib for v in f.verts)
for v in vs:
    t,_=loc(v.co.x,v.co.y);v.co.z=ZF+(IZ-ZF)*min(max(t,0),1)
kill=[]
for f in bm.faces:
    if f.material_index!=iw:continue
    c=f.calc_center_median();t,e=loc(c.x,c.y)
    if 0.01<t<0.99 and e<4 and c.z>ZF+(IZ-ZF)*t+0.05:kill.append(f)
bmesh.ops.delete(bm,geom=kill,context='FACES');bm.to_mesh(me);print('FLAT',len(vs),'TRUSSFACES',len(kill))
bpy.ops.export_scene.gltf(filepath=D+'optus_roof2.glb',export_format='GLB')
