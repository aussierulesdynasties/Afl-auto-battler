# blender -b out/r13/traeger.blend --python turn.py -- OUTDIR [N]
# Turntable film frames: N frames on a full circle round the oval centre (radius 235 m, height 105 m, aim (0,5,0)),
# the same orbit (mode 'orbit'), or mode 'west': a slow pass along the stand and clubrooms. Same orbit as the four turntable stills in shots.py.
import bpy,sys,os,math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];OUT=a[0];N=int(a[1]) if len(a)>1 else 120;MODE=a[2] if len(a)>2 else 'orbit';os.makedirs(OUT,exist_ok=True)
sc=bpy.context.scene;sc.render.film_transparent=False;cam=sc.camera
sc.render.resolution_x=1280;sc.render.resolution_y=720
g=bpy.data.collections.get('ground')
for o in (g.objects if g else []):o.hide_render=False
for i in range(N):
    if MODE=='orbit':
        r=math.radians(200+360*i/N);eye=Vector((235*math.cos(r),235*math.sin(r),105));tg=Vector((0,5,0));lens=28
    else:
        # pass along the west side: eye 40 m out on the ground at 12 m up, sliding south to north, aimed at the stand
        y=-45+130*i/(N-1);eye=Vector((-28,y,12));tg=Vector((-72,y+6,5));lens=30
    cam.location=eye;cam.rotation_euler=(tg-eye).to_track_quat('-Z','Y').to_euler()
    cam.data.lens=lens;cam.data.sensor_width=36;cam.data.shift_x=cam.data.shift_y=0;cam.data.clip_start=0.1
    sc.render.filepath=os.path.join(OUT,'f%03d.png'%i);bpy.ops.render.render(write_still=True)
print('TURN OK',N)
