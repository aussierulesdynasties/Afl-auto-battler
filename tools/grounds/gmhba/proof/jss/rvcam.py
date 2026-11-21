import bpy,math,mathutils,sys,numpy as np
a=sys.argv[sys.argv.index('--')+1:];src,out,camf=a[0],a[1],a[2];sx=float(a[3]) if len(a)>3 else 1
d=np.load(camf);C,Rm,f,cx,cy,W,H=d['C'],d['R'],float(d['f']),float(d['cx']),float(d['cy']),int(d['W']),int(d['H'])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
sc=bpy.context.scene;w=bpy.data.worlds.new('w');w.color=(0.6,0.7,0.85);sc.world=w
s=bpy.data.objects.new('s',bpy.data.lights.new('s','SUN'));s.data.energy=4;az=math.radians(160);el=math.radians(35);s.rotation_euler=mathutils.Vector((-math.cos(el)*math.cos(az),-math.cos(el)*math.sin(az),-math.sin(el))).to_track_quat('-Z','Y').to_euler();sc.collection.objects.link(s)
f2=bpy.data.objects.new('f',bpy.data.lights.new('f','SUN'));f2.data.energy=0.4;f2.rotation_euler=(0.8,-0.3,-2.3);sc.collection.objects.link(f2)
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=int(W*sx);sc.render.resolution_y=int(H*sx)
c=bpy.data.objects.new('c',bpy.data.cameras.new('c'));cd=c.data;cd.clip_end=5000;cd.sensor_fit='HORIZONTAL' if W>=H else 'VERTICAL';cd.sensor_width=36;cd.sensor_height=36
cd.lens=f/max(W,H)*36;cd.shift_x=(W/2-cx)/max(W,H)*-1;cd.shift_y=(cy-H/2)/max(W,H)
M=Rm.T@np.diag([1,-1,-1]);mw=mathutils.Matrix.Identity(4)
for i in range(3):
    for j in range(3):mw[i][j]=M[i,j]
    mw[i][3]=C[i]
c.matrix_world=mw;sc.collection.objects.link(c);sc.camera=c;sc.render.filepath=out;bpy.ops.render.render(write_still=True)
