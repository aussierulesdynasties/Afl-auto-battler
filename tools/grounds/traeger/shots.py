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
    ('tower_full',(-20,-40,24),(-58.5,-72.5,26),22),
    ('tower_head',(-30,-50,52),(-58.5,-72.5,49),45),
    ('fl_pole_head',(-25,72,52),(-52,97.5,48),45),
    ('fl_lattice',(-35,55,26),(-61,75,24),30),
    ('lattice_mast',(40,-35,16),(70,-55,15),30),
    ('south_wing',(-50,-26,6),(-70,-12,4),34),
    ('stair_tower',(-62,-30,7),(-76,-16,4),34),
    ('under_deck',(-58,6,2),(-70,6,1.5),30),
    ('join_wing_deck',(-60,-4,4),(-68.6,-1,3),45),
    ('join_stand_club',(-50,30,8),(-66,24,5),40),
    ('fence_bow_pal',(-60,-35,4),(-78,-18,1),30),
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
