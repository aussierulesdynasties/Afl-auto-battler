# blender -b w3t.blend --python tt.py -- JOB OUTDIR      JOB: stills | close | mp4
import bpy,math,sys,os
from mathutils import Vector
argv=sys.argv[sys.argv.index('--')+1:];JOB=argv[0];OUT=os.path.abspath(argv[1])
sc=bpy.context.scene;cam=sc.camera;cd=cam.data
cd.shift_x=0;cd.shift_y=0;cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.clip_start=0.1
sc.render.film_transparent=False
CEN=Vector((144,77,0))
def look(eye,tgt):
    cam.location=eye;cam.rotation_euler=(tgt-eye).to_track_quat('-Z','Y').to_euler()
def orbit(t,r=260,h=110):
    look(CEN+Vector((r*math.cos(t),r*math.sin(t),h)),CEN+Vector((0,0,4)))
def still(path):
    sc.render.image_settings.file_format='PNG';sc.render.filepath=path;bpy.ops.render.render(write_still=True)
if JOB=='stills':
    sc.render.resolution_x,sc.render.resolution_y=1600,900;sc.cycles.samples=48;cd.lens=30
    for k,deg in enumerate((0,90,180,270)):
        orbit(math.radians(deg));still(os.path.join(OUT,'whitten_turntable_%03d.png'%deg))
elif JOB=='close':
    sc.render.resolution_x,sc.render.resolution_y=1600,900;sc.cycles.samples=64;cd.lens=28
    for name in (argv[2:] or ('ejs_stand','ejw_stand','main_stand','south_bank','north_terrace','apron_dirt')):
        ob=bpy.data.objects[name];vs=[ob.matrix_world@v.co for v in ob.data.vertices]
        bc=sum(vs,Vector())/len(vs);c=min(vs,key=lambda v:(v-bc).xy.length)  # a real point on the part near its middle
        d=(Vector((c.x,c.y,0))-CEN);d.z=0;d.normalize()
        sg=-1 if name=='north_terrace' else 1  # the rock slope faces away from the ground: film it from outside
        tgt=Vector((c.x,c.y,2.0 if sg<0 else 4.0));look(tgt-sg*d*28+Vector((0,0,6 if sg<0 else 4)),tgt)
        still(os.path.join(OUT,'whitten_closeup_%s.png'%name))
elif JOB=='mp4':
    sc.render.resolution_x,sc.render.resolution_y=1280,720;sc.cycles.samples=24;cd.lens=30
    N=120;sc.frame_start=1;sc.frame_end=N;sc.render.fps=24
    for f in range(1,N+1):
        orbit(2*math.pi*(f-1)/N);cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f)
    if cam.animation_data and cam.animation_data.action:
        for fc in getattr(cam.animation_data.action,'fcurves',[]):
            for kp in fc.keyframe_points:kp.interpolation='LINEAR'
    ims=sc.render.image_settings
    if hasattr(ims,'media_type'):ims.media_type='VIDEO'
    ims.file_format='FFMPEG';sc.render.ffmpeg.format='MPEG4';sc.render.ffmpeg.codec='H264'
    sc.render.ffmpeg.constant_rate_factor='HIGH';sc.render.filepath=os.path.join(OUT,'whitten_exterior_')
    bpy.ops.render.render(animation=True)
