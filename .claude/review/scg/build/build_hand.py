# Blender: SCG exterior from scg_mesh.json -> GLB, plus a render from the photo's matched camera.
import bpy,bmesh,json,sys,math
from mathutils import Matrix,Vector
args=sys.argv[sys.argv.index('--')+1:];S=args[0];OUTGLB=args[1];REND=args[2];CJ=args[3] if len(args)>3 else 'cam.json'
D=json.load(open(S+'/scg_mesh.json'));cam=json.load(open(S+'/'+CJ))
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('SCG');ob=bpy.data.objects.new('SCG_exterior',me);bpy.context.scene.collection.objects.link(ob)
def img(n):return bpy.data.images.load(S+'/out/'+n)
def mat(name,col=None,tex=None,rough=0.85):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value=rough
    if tex:
        t=nt.nodes.new('ShaderNodeTexImage');t.image=img(tex)
        b.inputs['Base Color'].default_value=(0,0,0,1);b.inputs['Specular IOR Level'].default_value=0.0
        nt.links.new(t.outputs['Color'],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=1.0   # the photo already holds the light
    else:b.inputs['Base Color'].default_value=(*[(c/255)**2.2 for c in col],1)
    me.materials.append(m);return len(me.materials)-1
SCL=json.load(open(S+'/out/tex/scale.json'))
MI={}
for k in D['MATS']:
    m=bpy.data.materials.new(k);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(S+'/out/tex/%s.png'%k);nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
    b.inputs['Roughness'].default_value=0.15 if k in('glass','glassd','glassroof','screen') else (0.5 if k in('roof','fascia','hroof','facade2') else 0.85)
    if k in('glass','glassd'):b.inputs['Metallic'].default_value=0.3
    if k=='lamp':nt.links.new(t.outputs['Color'],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=0.6
    me.materials.append(m);MI[k]=len(me.materials)-1
bm=bmesh.new();vs=[bm.verts.new(v) for v in D['V']];uvl=bm.loops.layers.uv.new('UV')
PC=Vector((0.94,-11.82,0))
PLANAR=('grass','ground','apron')
import os
SEATQ=[]
for f in D['F']:
    if f['m'] in('seat','seatm'):SEATQ.append((f['m'],[D['V'][i] for i in f['v']]));f['m']='conc'
DEC=json.load(open(S+'/decals.json')) if os.path.exists(S+'/decals.json') else {}
for f in D['F']:
    try:fa=bm.faces.new([vs[i] for i in f['v']])
    except ValueError:continue
    m=f['m'];fa.material_index=MI[m];tu,tv=SCL[m];fa.normal_update();n=fa.normal
    cen=fa.calc_center_median();rad=Vector((cen.x-PC.x,cen.y-PC.y,0));rad=rad.normalized() if rad.length>1e-6 else Vector((1,0,0))
    tan=Vector((-rad.y,rad.x,0))
    ac=math.atan2(cen.y-PC.y,cen.x-PC.x)
    for l in fa.loops:
        p=l.vert.co;a=math.atan2(p.y-PC.y,p.x-PC.x)
        while a-ac>math.pi:a-=2*math.pi
        while a-ac<-math.pi:a+=2*math.pi
        r=(Vector((p.x,p.y,0))-PC).length
        if m in DEC:
            dd=DEC[m];u=((p.x-dd['o'][0])*dd['d'][0]+(p.y-dd['o'][1])*dd['d'][1])/dd['w'];v=(p.z-dd['z0'])/(dd['z1']-dd['z0']);l[uvl].uv=(u,v);continue
        if m in PLANAR:u,v=p.x,p.y
        elif m in('seat','seatm'):
            nr=n.dot(rad);s_=math.hypot(nr,n.z) or 1;rf=100.0 if m=='seat' else 86.0;u,v=a*rf,(r*n.z-p.z*nr)/s_   # one radius per seat material (median r): aisles radial and continuous   # rows along the arc, pitch along the rake
        elif abs(n.z)>0.75:u,v=a*r,r                                # roofs, slabs: seams run round the ground
        elif abs(n.dot(rad))>=abs(n.dot(tan)):u,v=a*r,p.z         # walls facing out or in
        else:u,v=r,p.z                                             # side walls of fins and boxes
        l[uvl].uv=(u/tu,v/tv)
bm.normal_update();bm.to_mesh(me);me.update()
exec(open(S+'/seats3d.py').read())
# raised lettering (signs.json from geo.py): Liberation Sans Bold, extruded, converted to mesh, joined into the model
SFONT=bpy.data.fonts.load(S+'/fonts/LiberationSans-Bold.ttf')   # SIL OFL 1.1, Arial-design grotesque: matches the SCG sign capitals (photo nrl.com 2022 + refs3/100)
if os.path.exists(S+'/signs.json'):
    for sg in json.load(open(S+'/signs.json')):
        cu=bpy.data.curves.new('sign','FONT');cu.body=sg['txt'];cu.font=SFONT;cu.align_x='CENTER';cu.size=1.0;cu.extrude=sg['d']/2
        to=bpy.data.objects.new('sign',cu);bpy.context.scene.collection.objects.link(to)
        dg=bpy.context.evaluated_depsgraph_get();tm=bpy.data.meshes.new_from_object(to.evaluated_get(dg));bpy.data.objects.remove(to)
        xs=[v.co.x for v in tm.vertices];sc=sg['w']/(max(xs)-min(xs));x0=(max(xs)+min(xs))/2;ymin=min(v.co.y for v in tm.vertices);hh=(max(v.co.y for v in tm.vertices)-ymin)*sc
        rx,ry=-sg['ny'],sg['nx']   # reading direction: right of a viewer facing the sign
        for v in tm.vertices:
            a,b,c=(v.co.x-x0)*sc,(v.co.y-ymin)*sc*sg.get('h',hh)/hh,v.co.z*sc
            v.co=Vector((sg['x']+rx*a+sg['nx']*c,sg['y']+ry*a+sg['ny']*c,sg['z']+0.15+b))
        tm.materials.append(me.materials[MI[sg['m']]]);so=bpy.data.objects.new('signm',tm);bpy.context.scene.collection.objects.link(so)
        bpy.ops.object.select_all(action='DESELECT');so.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.join()
        print('SIGN',sg['txt'],'height %.2f m'%sg.get('h',hh))
# GLB in metres, Godot Y-up handled by exporter
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
for so_ in SEATOBJ:so_.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUTGLB,export_format='GLB',use_selection=True,export_yup=True,export_gpu_instances=True,export_gn_mesh=True)
# matched camera
p=cam['p'];W,H=cam.get('W',1200),cam.get('H',675)
def R(yaw,pitch,roll):
    import numpy as np
    exec_globals={}
    return None
import numpy as np
src=open(S+'/cam.py').read();g={};exec(src.split('def proj')[0].replace("G=json.load(open('osm/geo.json'))['geo']","G={}").replace("TOW={k:G[k][0] for k in G if k[0]=='T'}",""),g)
Rm=g['R'](*p[3:6]);right,up,fwd=Rm[0],Rm[1],Rm[2]
cd=bpy.data.cameras.new('cam');co=bpy.data.objects.new('cam',cd);bpy.context.scene.collection.objects.link(co)
co.matrix_world=Matrix(((right[0],up[0],-fwd[0],p[0]),(right[1],up[1],-fwd[1],p[1]),(right[2],up[2],-fwd[2],p[2]),(0,0,0,1)))
cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=p[6]*36/W;cd.shift_x=-(p[7]-W/2)/W;cd.shift_y=(p[8]-H/2)/W;cd.clip_end=3000
sc=bpy.context.scene;sc.camera=co;sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.film_transparent=True
sc.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
sun=bpy.data.lights.new('sun','SUN');sun.energy=2.6;so=bpy.data.objects.new('sun',sun);sc.collection.objects.link(so);so.rotation_euler=(math.radians(40),0,math.radians(-60))
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.45;w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.8,0.85,0.9,1)
sc.view_settings.view_transform='Standard'
sc.render.filepath=REND;bpy.ops.render.render(write_still=True)
print('DONE',len(me.polygons))
