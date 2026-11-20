# blender -b --python turn.py -- OUTDIR NFRAMES   (NFRAMES=0: facade close-ups only)
import bpy,sys,os,math
from mathutils import Vector
argv=sys.argv[sys.argv.index('--')+1:]
out,n=argv[0],int(argv[1])
sys.argv=[sys.argv[0],'--','-']
HERE=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE,'build.py')).read())
sc=bpy.context.scene
sc.render.film_transparent=False;sc.world=sc.world or bpy.data.worlds.new('w');sc.world.color=(0.55,0.68,0.85)
sc.render.engine='BLENDER_WORKBENCH';sc.view_settings.view_transform='Standard';sh=sc.display.shading;sh.light='FLAT';sh.color_type='TEXTURE';sh.show_shadows=True
sh.shadow_intensity=0.55;sc.display.light_direction=(0.35,0.45,0.82);sh.show_cavity=True;sh.background_type='WORLD'
cd=bpy.data.cameras.new('orb');cd.clip_end=3000
co=bpy.data.objects.new('orb',cd);bpy.context.collection.objects.link(co);sc.camera=co
def shot(pos,tgt,path,lens):
    pos,tgt=Vector(pos),Vector(tgt);cd.lens=lens
    co.location=pos;co.rotation_euler=(tgt-pos).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=path;bpy.ops.render.render(write_still=True)
if n:
    sc.render.resolution_x=1280;sc.render.resolution_y=720
    a0=math.atan2(cam['p'][1]-1,cam['p'][0]-9)
    for i in range(n):
        a=a0+2*math.pi*i/n
        shot((9+300*math.cos(a),1+300*math.sin(a),150),(9,1,8),os.path.join(out,'f%03d.png'%i),28)
else:
    sc.render.resolution_x=1920;sc.render.resolution_y=1080
    shot(EP(26,-34,9),EP(26,0,7),os.path.join(out,'close_emu.png'),35)
    shot(NP(30,-40,10),NP(30,0,12),os.path.join(out,'close_north.png'),35)
    shot(SBP(0,30,8),SBP(0,0,14),os.path.join(out,'close_scoreboard.png'),35)
