import bpy,json,sys,math,mathutils,numpy as np
argv=sys.argv[sys.argv.index('--')+1:];OUT=argv[0];GLB=argv[1] if len(argv)>1 and argv[1]!='-' else ''
D=json.load(open('model.json'));cam=json.load(open('cam4.json'))['q']
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
mats={}
for k,c in D['mats'].items():
    m=bpy.data.materials.new(k);col=[(x/255)**2.2 for x in c]+[1];m.diffuse_color=col;m.use_nodes=True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=col;m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=0.8;mats[k]=m
import os
TEX={'multi':(os.path.abspath('seats_multi.png'),32.0),'banner':(os.path.abspath('z/banner_corroboree.png'),0)}  # image, metres covered by one tile (0.5 m seat rows)
for k,(img,_) in TEX.items():
    m=mats[k];nt=m.node_tree;ti=nt.nodes.new('ShaderNodeTexImage');ti.image=bpy.data.images.load(img);ti.interpolation='Closest' if k=='multi' else 'Linear'
    nt.links.new(ti.outputs['Color'],nt.nodes['Principled BSDF'].inputs['Base Color'])
for o in D['objs']:
    me=bpy.data.meshes.new(o['name']);me.from_pydata(o['v'],[],o['f']);me.validate();me.update()
    if 'uv' in o:
        uvl=me.uv_layers.new(name='UV')
        for poly in me.polygons:
            for li in poly.loop_indices:uvl.data[li].uv=o['uv'][me.loops[li].vertex_index]
    elif o['mat'] in TEX:
        sz=TEX[o['mat']][1];uvl=me.uv_layers.new(name='UV')
        V=np.array(o['v']);n=o['n'] or 1;m_=len(V)//n;G=V.reshape(m_,n,3)
        U=np.zeros((m_,n));W=np.zeros((m_,n))
        U[1:]=np.cumsum(np.linalg.norm(np.diff(G,axis=0),axis=2),axis=0);W[:,1:]=np.cumsum(np.linalg.norm(np.diff(G,axis=1),axis=2),axis=1)
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi=me.loops[li].vertex_index;uvl.data[li].uv=(U[vi//n,vi%n]/sz,W[vi//n,vi%n]/51.0)
    ob=bpy.data.objects.new(o['name'],me);ob.data.materials.append(mats[o['mat']]);sc.collection.objects.link(ob)
# matched camera
C=np.array(cam[:3]);yaw,pit,rol,FO,CX,CY=cam[3:9]
cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pit),math.sin(pit);cr,sr=math.cos(rol),math.sin(rol)
f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);R1=cr*r+sr*u;U1=-sr*r+cr*u
Mw=mathutils.Matrix([[R1[0],U1[0],-f[0]],[R1[1],U1[1],-f[1]],[R1[2],U1[2],-f[2]]])
cd=bpy.data.cameras.new('cam');cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=FO*36/1920
cd.shift_x=-(CX-960)/1920;cd.shift_y=(CY-640)/1920;cd.clip_end=3000;cd.clip_start=20
co=bpy.data.objects.new('cam',cd);co.matrix_world=mathutils.Matrix.Translation(C.tolist())@Mw.to_4x4();sc.collection.objects.link(co);sc.camera=co

# ---- project the reference photo onto faces its camera sees nearly head-on, unblocked and not behind trees
from bpy_extras.object_utils import world_to_camera_view
sc.render.resolution_x=1920;sc.render.resolution_y=1280
_vi=bpy.data.images.load(os.path.abspath('z/vegmask.png'));VEG=(np.array(_vi.pixels[:]).reshape(1280,1920,-1)[::-1,:,0]*255).astype(int)
NOPROJ={'turf','pave','hill','banner'}
pm=bpy.data.materials.new('photo');pm.use_nodes=True;pn=pm.node_tree;pt=pn.nodes.new('ShaderNodeTexImage');pt.image=bpy.data.images.load(os.path.abspath('photo.png'))
pn.links.new(pt.outputs['Color'],pn.nodes['Principled BSDF'].inputs['Base Color']);pn.nodes['Principled BSDF'].inputs['Roughness'].default_value=0.9
# subdivide every mesh (simple) so photo projection and tree masking work on ~1-2 m cells
for ob in [o for o in sc.objects if o.type=='MESH']:
    if ob.data.materials[0].name in NOPROJ:continue
    lv=2 if len(ob.data.polygons)>60 else 3
    md=ob.modifiers.new('sub','SUBSURF');md.subdivision_type='SIMPLE';md.levels=lv;md.render_levels=lv
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier='sub')
dg=bpy.context.evaluated_depsgraph_get();camp=co.matrix_world.translation.copy();nproj=0;ntot=0
for ob in [o for o in sc.objects if o.type=='MESH']:
    if ob.data.materials[0].name in NOPROJ:continue
    me=ob.data;me.materials.append(pm)
    uvl=me.uv_layers.get('UV') or me.uv_layers.new(name='UV')
    for poly in me.polygons:
        ntot+=1
        fc=poly.center;dv=camp-fc;dist=dv.length;dv.normalize()
        if abs(poly.normal.dot(dv))<0.3:continue
        hit,loc,nrm,idx,hob,_=sc.ray_cast(dg,camp,-dv,distance=dist+1)
        if not hit or hob.name!=ob.name or idx!=poly.index:continue
        uvs=[world_to_camera_view(sc,co,me.vertices[me.loops[li].vertex_index].co) for li in poly.loop_indices]
        cc=world_to_camera_view(sc,co,fc);pts=uvs+[cc];g=0
        for q in pts:
            px=int(q.x*1919);py=int((1-q.y)*1279)
            if 0<=px<1920 and 0<=py<1280 and VEG[py,px]>0:g+=1
        if g*2>len(pts):continue
        for li,q in zip(poly.loop_indices,uvs):uvl.data[li].uv=(q.x,q.y)
        poly.material_index=1;nproj+=1
print('PROJECTED',nproj,'of',ntot)
sc.render.resolution_x=1920;sc.render.resolution_y=1280;sc.render.film_transparent=True
sc.render.engine='BLENDER_WORKBENCH';sh=sc.display.shading;sh.light='STUDIO';sh.color_type='TEXTURE';sh.show_shadows=True;sh.show_cavity=True
sc.render.filepath=OUT;bpy.ops.render.render(write_still=True)
if len(argv)>2:
    import random;random.seed(1)
    for ob in sc.objects:
        if ob.type=='MESH':ob.color=(random.random(),random.random(),random.random(),1)
    sh.light='FLAT';sh.color_type='OBJECT';sh.show_shadows=False;sh.show_cavity=False;sc.view_settings.view_transform='Standard'
    sc.render.filepath=argv[2];bpy.ops.render.render(write_still=True)
if GLB:bpy.ops.object.select_all(action='DESELECT');[o.select_set(o.type=='MESH') for o in sc.objects];bpy.ops.export_scene.gltf(filepath=GLB,use_selection=True,export_format='GLB')
