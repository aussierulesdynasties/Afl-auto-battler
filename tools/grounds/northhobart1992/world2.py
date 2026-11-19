# Whole North Hobart Oval, 1992: Gorringe (gor.py, local frame placed in world) + geo2.json + hand-made ground.
# usage: blender -b --factory-startup --python world2.py -- NH MODE OUT [scale]
#   MODE aerial | gor | tt | close | glb
import bpy,bmesh,sys,json,math,numpy as np
from mathutils import Matrix,Vector
a=sys.argv[sys.argv.index('--')+1:];NH,MODE,OUT=a[0],a[1],a[2];SC=float(a[3]) if len(a)>3 else 0.25
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
exec(open(NH+'/blib.py').read());exec(open(NH+'/gor.py').read())
before=set(bpy.data.objects);gor_build(addobj)
AX,NY=GOR_AX,GOR_NY
Mg=Matrix(((AX[0],NY[0],0,GOR_F0[0]),(AX[1],NY[1],0,GOR_F0[1]),(0,0,1,0),(0,0,0,1)))
for o in set(bpy.data.objects)-before:o.matrix_world=Mg
G=json.load(open(NH+'/geo2.json'))
import os
for name,faces in G['objs'].items():
    if name=='ryde_nab' and os.environ.get('NAB')!='1':continue
    addobj(name,faces,double=True,uvfit=(name in('ne_board_face','ryde_nab')))
def ground(name,pts,z,mat,ud=None,vd=None):
    bm=bmesh.new();uvl=bm.loops.layers.uv.new();vs=[bm.verts.new((x,y,z)) for x,y in pts];f=bm.faces.new(vs)
    bmesh.ops.triangulate(bm,faces=[f])
    su,sv=SIZES[mat];ud=Vector(ud or (1,0,0));vd=Vector(vd or (0,1,0))
    for f in bm.faces:
        if f.normal.z<0:f.normal_flip()
        for l in f.loops:p=l.vert.co;l[uvl].uv=(p.dot(ud)/su,p.dot(vd)/sv)
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);o.data.materials.append(TM(mat));return o
# ground out to the outer boundary, with no field inside the fence (director 2026-11-18: "Leave field out")
def ground_tris(name,tris,z,mat):
    bm=bmesh.new();uvl=bm.loops.layers.uv.new();su,sv=SIZES[mat]
    for t in tris:
        f=bm.faces.new([bm.verts.new((x,y,z)) for x,y in t])
        f.normal_update()
        if f.normal.z<0:f.normal_flip()
        for l in f.loops:p=l.vert.co;l[uvl].uv=(p.x/su,p.y/sv)
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-4)
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);o.data.materials.append(TM(mat));return o
ground_tris('ground',G['ground_tris'],0.0,'asphalt')
W_=json.load(open(NH+'/world.json'));az,el=map(math.radians,W_['sun'])
sv=Vector((math.sin(az)*math.cos(el),math.cos(az)*math.cos(el),math.sin(el)))
ld=bpy.data.lights.new('sun','SUN');ld.energy=4.0;ld.angle=math.radians(0.5);lo=bpy.data.objects.new('sun',ld);sc.collection.objects.link(lo)
lo.rotation_euler=sv.to_track_quat('Z','Y').to_euler()
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs[0].default_value=(0.55,0.65,0.8,1);bg.inputs[1].default_value=0.7
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.view_settings.view_transform='AgX';sc.cycles.samples=24
cd=bpy.data.cameras.new('cam');co=bpy.data.objects.new('cam',cd);sc.collection.objects.link(co);sc.camera=co;cd.clip_start=1;cd.clip_end=5000
def look(eye,tgt,lens,Wp,Hp):
    eye=Vector(eye);d=(Vector(tgt)-eye);co.location=eye;co.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=lens;sc.render.resolution_x,sc.render.resolution_y=Wp,Hp
def render(fn):sc.render.filepath=fn;bpy.ops.render.render(write_still=True)
if MODE=='glb':
    bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB');sys.exit(0)
if MODE=='aerial':
    cam=W_['cam'];p=cam['p'];U0,V0,F=cam['U0'],cam['V0'],cam['F'];cx,cy,cw,ch=cam['crop']
    def Rm(om,ph,ka):
        Rx=np.array([[1,0,0],[0,math.cos(om),-math.sin(om)],[0,math.sin(om),math.cos(om)]]);Ry=np.array([[math.cos(ph),0,math.sin(ph)],[0,1,0],[-math.sin(ph),0,math.cos(ph)]])
        Rz=np.array([[math.cos(ka),-math.sin(ka),0],[math.sin(ka),math.cos(ka),0],[0,0,1]]);return Rz@Ry@Rx
    R=Rm(*p[3:6]);C=np.array(p[:3])
    co.matrix_world=Matrix([[*R[0],C[0]],[*R[1],C[1]],[*R[2],C[2]],[0,0,0,1]])
    Wp,Hp=int(cw*SC),int(ch*SC);sc.render.resolution_x,sc.render.resolution_y=Wp,Hp
    cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=36*F*SC/Wp;cd.clip_end=5000;cd.clip_start=10
    ppx=(U0+p[6]-cx)*SC;ppy=(V0+p[7]-cy)*SC;cd.shift_x=(Wp/2-ppx)/Wp;cd.shift_y=(ppy-Hp/2)/Wp
    sc.view_settings.view_transform='Standard';sc.render.film_transparent=bool(os.environ.get('TRANSP'))
    if os.environ.get('BORDER'):
        x0,y0,x1,y1=map(float,os.environ['BORDER'].split(','));r=sc.render;r.use_border=True;r.use_crop_to_border=True
        r.border_min_x,r.border_max_x=x0/cw,x1/cw;r.border_min_y,r.border_max_y=1-y1/ch,1-y0/ch
    render(OUT)
elif MODE=='top':
    # straight down, north up, orthographic, same box as the rectified 1992 aerial (x -140..125, y -145..115, SC m/px)
    X0,X1,Y0,Y1=-140,125,-145,115;co.location=((X0+X1)/2,(Y0+Y1)/2,300);co.rotation_euler=(0,0,0)
    cd.type='ORTHO';cd.sensor_fit='HORIZONTAL';cd.ortho_scale=X1-X0;cd.clip_end=1000
    sc.render.resolution_x,sc.render.resolution_y=int((X1-X0)/SC),int((Y1-Y0)/SC);sc.render.film_transparent=True
    sc.view_settings.view_transform='Standard';render(OUT)
elif MODE=='gor':
    c=json.load(open(NH+'/cam_gor.json'));R=Matrix(c['R']);Cc=Vector(c['C'])
    Rb=R.transposed()@Matrix(((1,0,0),(0,-1,0),(0,0,-1)))
    co.matrix_world=Mg@(Matrix.Translation(Cc)@Rb.to_4x4())
    sc.render.resolution_x,sc.render.resolution_y=int(c['W']*SC),int(c['H']*SC);cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=36*c['f']/c['W']
    render(OUT)
elif MODE=='tt':
    for k,deg in enumerate((200,290,20,110)):
        t=math.radians(deg);look((-17.2+290*math.cos(t),-4.4+290*math.sin(t),145),(-17.2,-4.4,4),35,1600,1000);render(OUT.replace('#',str(k)))
elif MODE=='mp4':
    sc.render.engine='BLENDER_EEVEE';sc.frame_start,sc.frame_end=1,240;sc.render.fps=30
    look((0,0,0),(0,0,-1),35,1280,800)
    tg=bpy.data.objects.new('tgt',None);sc.collection.objects.link(tg);tg.location=(-17.2,-4.4,4)
    k=co.constraints.new('TRACK_TO');k.target=tg;k.track_axis='TRACK_NEGATIVE_Z';k.up_axis='UP_Y'
    for fr in range(1,241):
        t=math.radians(200+360*(fr-1)/240);co.location=(-17.2+290*math.cos(t),-4.4+290*math.sin(t),145);co.keyframe_insert('location',frame=fr)
    if OUT.endswith('.mp4'):
        sc.render.image_settings.media_type='VIDEO';sc.render.image_settings.file_format='FFMPEG';sc.render.ffmpeg.format='MPEG4';sc.render.ffmpeg.codec='H264'
        sc.render.ffmpeg.constant_rate_factor='HIGH'
    else:
        sc.render.image_settings.file_format='PNG';sc.render.use_overwrite=False;sc.render.use_placeholder=True
    sc.render.filepath=OUT;bpy.ops.render.render(animation=True)
elif MODE=='sb':
    look((73.03-0.987*35,20.28-0.161*35,7.0),(73.03,20.28,8.0),40,1200,1000);render(OUT)
elif MODE=='close':
    gc=Mg@Vector((20.6,-14,5.5));tg=Mg@Vector((20.6,1,6.0));look(tuple(gc),tuple(tg),30,1600,1000);render(OUT)
