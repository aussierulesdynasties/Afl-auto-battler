# blender -b out/r4/traeger.blend --python shots.py -- OUTDIR
# Proof stills: 4 turntable views plus one close camera per part (look-at cameras, world metres).
import bpy,sys,os,math
from mathutils import Vector
OUT=sys.argv[sys.argv.index('--')+1];os.makedirs(OUT,exist_ok=True)
S=[]
for i,a in enumerate((200,290,20,110)):           # turntable: 4 quarters around the oval centre
    r=math.radians(a);S.append(('turn_%d'%i,(235*math.cos(r),235*math.sin(r),105),(0,5,0),28))
S+=[('stand',(-25,-8,16),(-84,0,6),32),
    ('stand_facade_close',(-57,4,8.2),(-77.5,4,8.2),40),
    ('roof',(-35,-55,48),(-85,0,9),38),
    ('clubrooms',(-28,38,11),(-68,52,4),32),
    ('clubrooms_close',(-48,46,4),(-66,53,2.5),38),
    ('tower_full',(-22,-42,22),(-62,-81,26),22),
    ('tower_head',(-36,-63,50),(-62,-81,49),45),
    ('lattice_mast',(40,-35,16),(70,-55,15),30),
    ('scoreboard',(34,58,6),(34,87,5),40),
    ('pole_sign',(42,62,20),(56,83,19.5),40),
    ('fence',(-20,70,3),(-35,96,0.8),32),
    ('fence_east',(48,-22,2.5),(70,-40,0.7),32)]
sc=bpy.context.scene;sc.render.film_transparent=False;cam=sc.camera;   # the world's sky colour, not a black void
sc.render.resolution_x=1500;sc.render.resolution_y=1000
g=bpy.data.collections.get('ground')
for o in (g.objects if g else []):o.hide_render=False
for n,eye,tg,lens in S:
    cam.location=Vector(eye);cam.rotation_euler=(Vector(tg)-Vector(eye)).to_track_quat('-Z','Y').to_euler()
    cam.data.lens=lens;cam.data.sensor_width=36;cam.data.shift_x=cam.data.shift_y=0;cam.data.clip_start=0.1
    sc.render.filepath=os.path.join(OUT,n+'.png');bpy.ops.render.render(write_still=True);print('OK',n)
