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
TL=json.load(open('tex/tiles.json'))
MAP={'teal':'seats_teal','multi':'seats_multi','wseat':'seats_white','navy':'seats_navy','red':'seats_red','roofg':'roof_grey','pavroof':'roof_pav','facade':'bronze'}
def texname(o):
    if 'tex' in o:return o['tex']
    m=o['mat']
    if m=='white' and o['name'].endswith('_roof'):return 'roof_white'
    return MAP.get(m,m)
tmats={}
def tmat(t):
    if t in tmats:return tmats[t]
    m=bpy.data.materials.new('T_'+t);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes['Principled BSDF']
    ti=nt.nodes.new('ShaderNodeTexImage');ti.image=bpy.data.images.load(os.path.abspath(f'tex/{t}.png'));ti.interpolation='Linear'
    nt.links.new(ti.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=0.35 if t=='glass' else 0.85
    tmats[t]=m;return m
for o in D['objs']:
    me=bpy.data.meshes.new(o['name']);me.from_pydata(o['v'],[],o['f']);me.validate();me.update()
    if o.get('smooth'):
        for pg in me.polygons:pg.use_smooth=True
    t=texname(o);su,sv_=TL.get(t,(1,1));uvl=me.uv_layers.new(name='UV')
    if 'uv' in o:
        for poly in me.polygons:
            for li in poly.loop_indices:uvl.data[li].uv=o['uv'][me.loops[li].vertex_index]
    elif o['n']:
        # swept band: u = metres along the arc, v = metres along the profile
        V=np.array(o['v']);n=o['n'];m_=len(V)//n;G=V.reshape(m_,n,3)
        U=np.zeros((m_,n));Wd=np.zeros((m_,n))
        U[1:]=np.cumsum(np.linalg.norm(np.diff(G,axis=0),axis=2),axis=0);Wd[:,1:]=np.cumsum(np.linalg.norm(np.diff(G,axis=1),axis=2),axis=1)
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi=me.loops[li].vertex_index;uvl.data[li].uv=(U[vi//n,vi%n]/su,Wd[vi//n,vi%n]/sv_)
    else:
        # box mapping in metres: flat faces by plan x,y; walls by horizontal run and height
        for poly in me.polygons:
            nx,ny,nz=poly.normal
            for li in poly.loop_indices:
                p=me.vertices[me.loops[li].vertex_index].co
                if abs(nz)>0.7:uv=(p.x/su,p.y/sv_)
                else:
                    h=math.hypot(nx,ny) or 1;uv=((-ny*p.x+nx*p.y)/h/su,p.z/sv_)
                uvl.data[li].uv=uv
    ob=bpy.data.objects.new(o['name'],me);ob.data.materials.append(tmat(t));sc.collection.objects.link(ob)
# matched camera
C=np.array(cam[:3]);yaw,pit,rol,FO,CX,CY=cam[3:9]
cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pit),math.sin(pit);cr,sr=math.cos(rol),math.sin(rol)
f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);R1=cr*r+sr*u;U1=-sr*r+cr*u
Mw=mathutils.Matrix([[R1[0],U1[0],-f[0]],[R1[1],U1[1],-f[1]],[R1[2],U1[2],-f[2]]])
cd=bpy.data.cameras.new('cam');cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=FO*36/1920
cd.shift_x=-(CX-960)/1920;cd.shift_y=(CY-640)/1920;cd.clip_end=3000;cd.clip_start=20
co=bpy.data.objects.new('cam',cd);co.matrix_world=mathutils.Matrix.Translation(C.tolist())@Mw.to_4x4();sc.collection.objects.link(co);sc.camera=co

# sun: shadows on the reference turf run toward plan bearing 48 deg (from the SW), low sun
# no photo projection (director 2026-11-18: hand-made textures only); sun and sky light for a daylight look
sc.render.resolution_x=1920;sc.render.resolution_y=1280
sd=bpy.data.lights.new('sun','SUN');sd.energy=4.0;sd.angle=math.radians(1.5);so=bpy.data.objects.new('sun',sd);sc.collection.objects.link(so)
SUN_AZ=float(os.environ.get('SUN_AZ','-132'));SUN_EL=float(os.environ.get('SUN_EL','20'))
so.rotation_euler=(math.radians(90-SUN_EL),0,math.radians(SUN_AZ+90))
wd=bpy.data.worlds.new('w');sc.world=wd;wd.use_nodes=True;wd.node_tree.nodes['Background'].inputs['Color'].default_value=(0.55,0.65,0.8,1);wd.node_tree.nodes['Background'].inputs['Strength'].default_value=0.9
sc.render.resolution_x=1920;sc.render.resolution_y=1280;sc.render.film_transparent=True
sh=sc.display.shading
try:sc.render.engine='BLENDER_EEVEE'
except Exception:sc.render.engine='BLENDER_EEVEE_NEXT'
sc.view_settings.view_transform='Standard'
sc.render.filepath=OUT;bpy.ops.render.render(write_still=True)
if len(argv)>2:
    import random;random.seed(1)
    for ob in sc.objects:
        if ob.type=='MESH':ob.color=(random.random(),random.random(),random.random(),1)
    sh.light='FLAT';sh.color_type='OBJECT';sh.show_shadows=False;sh.show_cavity=False;sc.view_settings.view_transform='Standard'
    sc.render.filepath=argv[2];bpy.ops.render.render(write_still=True)
if GLB:bpy.ops.object.select_all(action='DESELECT');[o.select_set(o.type=='MESH') for o in sc.objects];bpy.ops.export_scene.gltf(filepath=GLB,use_selection=True,export_format='GLB')
