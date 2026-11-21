# Blender 5.2 builder: geo.py faces -> textured meshes (hand-made textures from tex.py), renders and GLB.
# usage: blender -b --python build.py -- <cmd> [out]   cmd: match | turn | close | glb
import sys,os,json,math
import bpy,bmesh
from mathutils import Matrix,Vector
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
import numpy as np,geo,cam
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['match']
CMD=argv[0];OUT=os.path.abspath(os.path.join(HERE,argv[1] if len(argv)>1 else 'render_'+CMD))
TEX=os.path.join(HERE,'..','tex');SPEC=json.load(open(os.path.join(TEX,'spec.json')))
# geo material -> texture, plus (u origin, v origin): 'face' starts the pattern at the face's own corner, 'world' at x/y/z = 0
MAP={'annex_roof':'corr_green','annex_wall':'render_white','board_back':'cladding_khaki','board_front':'board_front',
 'brick_red':'brick_red','cladding_grey':'cladding_grey','render_cream':'render_cream','render_white':'render_white','concrete':'concrete',
 'fence_hoarding':'fence_hoarding','fence_picket':'fence_picket','hut_wall':'corr_red','lamp_back':'lamp_back','lamp_face':'lamp_face',
 'nw_hall_roof':'corr_beige','nw_hall_wall':'brick_red','nw_link_roof':'roof_beige','nw_link_wall':'brick_red','nw_north_roof':'corr_zinc',
 'nw_north_wall':'render_cream','nw_wing_roof':'corr_slate','nw_wing_wall':'bluestone','red_roof':'corr_red','red_wall':'brick_red',
 'se_hut_roof':'corr_zinc','se_hut_wall':'corr_cream','ses_aisle':'stair_nosing','ses_tread':'concrete_dark','ses_riser':'concrete',
 'ses_backwall':'timber_darkgreen','ses_brick':'ses_podium','ses_cap':'render_cream','ses_column':'paint_cream','ses_cupola_roof':'lead_grey',
 'ses_cupola_wall':'cupola_louvre','ses_endwall':'brick_red','ses_gablet':'ses_gablet','ses_pediment':'ses_pediment','ses_rear':'ses_rear_bay',
 'ses_roof':'corr_red','ses_soffit':'timber_cream','steel':'steel_galv','terrace_tread':'terrace_tread','terrace_riser':'terrace_riser',
 'terrace_back':'concrete','tower_pole':'steel_white','wbcc_box':'cladding_charcoal','wbcc_boxroof':'render_white','wbcc_roof':'render_white',
 'wbcc_mural':'wbcc_mural','wbcc_upper':'wbcc_upper','ws_backwall':'ws_backwall','ws_brick':'brick_red','ws_cap':'concrete','ws_end':'corr_maroon',
 'ws_fascia':'cladding_charcoal','ws_post':'steel_dark','ws_rear':'ws_rear_bay','ws_rearroof':'corr_wsrear','ws_roof':'corr_zinc',
 'ws_seats':'seat_teal','ws_step':'cladding_grey','ws_under':'deck_grey','ses_fascia':'paint_cream','ses_sign':'ses_sign',
 'paint_yellow':'paint_yellow','crowd_a':'crowd_a','crowd_b':'crowd_b','crowd_c':'crowd_c','barrier':'steel_white','turf':'turf','goal_pad':'goal_pad','goal_post':'steel_white',
 'wbcc_mesh':'wbcc_mesh','wbcc_west_lo':'wbcc_west_lo','wbcc_south_lo':'wbcc_south_lo','wbcc_south_up':'wbcc_south_up','wbcc_soffit':'wbcc_soffit',
 'steel_dark':'steel_dark','sign_red':'sign_red','sign_blue':'sign_blue','sign_white':'sign_white','led_board':'led_board','sign_kiosk':'sign_kiosk',
 'steel_back':'steel_galv','nw_wing_front':'nw_wing_front','hut_green':'hut_green','roof_beige':'roof_beige','paint_cream':'paint_cream','hoard_red':'hoard_red','hoard_blue':'hoard_blue','hoard_teal':'hoard_teal'}
for k in SPEC:
    if k.startswith('bench_') or k.startswith('box_'): MAP[k]=k
FACE_ORIGIN={'ses_podium':('face','face'),'ses_rear_bay':('face','world'),'ws_rear_bay':('face','world'),'seat_teal':('world','face'),
             'terrace_riser':('world','face'),'fence_hoarding':('world','world'),'ws_backwall':('world','face')}
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
reset()
sc=bpy.context.scene
mats={}
def material(tname):
    if tname in mats: return mats[tname]
    s=SPEC[tname];m=bpy.data.materials.new(tname);m.use_nodes=True
    nt=m.node_tree;b=nt.nodes['Principled BSDF'];im=nt.nodes.new('ShaderNodeTexImage')
    im.image=bpy.data.images.load(os.path.join(TEX,s['img']));im.interpolation='Linear'
    nt.links.new(im.outputs['Color'],b.inputs['Base Color'])
    rough={'glass_dark':0.15,'wbcc_upper':0.2,'glass_ws':0.2,'board_front':0.3}.get(tname,0.8 if 'corr' not in tname else 0.7)
    b.inputs['Roughness'].default_value=rough
    if 'corr' in tname or 'steel' in tname: b.inputs['Metallic'].default_value=0.1
    if s.get('alpha'):
        nt.links.new(im.outputs['Alpha'],b.inputs['Alpha'])
        try: m.surface_render_method='DITHERED'
        except Exception: pass
        m.blend_method='CLIP' if hasattr(m,'blend_method') else None
    m.use_backface_culling=False
    mats[tname]=m;return m
def uv_for(P,n,tname):
    s=SPEC[tname];tw,th=s['tw'],s['th'];P=np.asarray(P)
    if abs(n[2])>0.97: t=np.array([1.0,0,0]);b=np.array([0,1.0,0])
    else:
        t=np.cross([0,0,1.0],n);t/=np.linalg.norm(t);b=np.cross(n,t);b/=np.linalg.norm(b)
    U=P@t;V=P@b
    if s['mode']=='fit':
        return np.stack([(U-U.min())/max(np.ptp(U),1e-6),(V-V.min())/max(np.ptp(V),1e-6)],1)
    uo,vo=FACE_ORIGIN.get(tname,('world','world'))
    if uo=='face': U=U-U.min()
    if vo=='face': V=V-V.min()
    return np.stack([U/tw,V/th],1)
RENDER_ONLY=('field','goals')   # the game draws its own ground and posts; the exterior GLB leaves them out
def build():
    for name,L in geo.parts.items():
        if not L: continue
        allp=np.array([q for pts,*_ in L for q in pts]);cen=allp.mean(0)
        me=bpy.data.meshes.new(name);bm=bmesh.new();uvl=bm.loops.layers.uv.new('UVMap')
        slot={}
        if CMD=='glb' and name in RENDER_ONLY: continue
        if CMD=='turnvid' and name=='terrace_rails': pass
        for pts,m,uvs in L:
            P=np.array(pts,float)
            if len(P)<3: continue
            n=np.zeros(3)
            for i in range(len(P)): n+=np.cross(P[i],P[(i+1)%len(P)])
            if np.linalg.norm(n)<1e-9: continue
            n/=np.linalg.norm(n)
            if abs(n[2])<0.97 and np.dot(n[:2],(P.mean(0)-cen)[:2])<0: n=-n   # face the outside of the part, so signs read the right way round
            tname=MAP[m]
            if tname not in slot: slot[tname]=len(slot)
            vs=[bm.verts.new(tuple(p)) for p in P]
            try: f=bm.faces.new(vs)
            except ValueError: continue
            f.material_index=slot[tname]
            UV=uv_for(P,n,tname) if uvs is None else (np.array(uvs,float) if SPEC[tname]['mode']=='fit' else np.array(uvs,float)/[SPEC[tname]['tw'],SPEC[tname]['th']])
            for lp,uv in zip(f.loops,UV): lp[uvl].uv=(float(uv[0]),float(uv[1]))
        bmesh.ops.triangulate(bm,faces=bm.faces[:],quad_method='BEAUTY',ngon_method='EAR_CLIP')
        bm.to_mesh(me);bm.free()
        ob=bpy.data.objects.new(name,me);sc.collection.objects.link(ob)
        for tname,i in sorted(slot.items(),key=lambda a:a[1]): me.materials.append(material(tname))
build()
# ---------- world, light, colour ----------
def setup_render(W,H,ground=True):
    sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('SAMPLES','48'));sc.cycles.use_denoising=True
    try:
        pr=bpy.context.preferences.addons['cycles'].preferences;pr.compute_device_type='OPTIX';pr.get_devices()
        for d in pr.devices: d.use=True
        sc.cycles.device='GPU'
    except Exception as e: print('cpu render',e)
    sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.resolution_percentage=100
    sc.view_settings.view_transform='Standard'
    w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True
    w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.55,0.68,0.9,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.9
    ld=bpy.data.lights.new('sun','SUN');ld.energy=3.2;ld.angle=math.radians(1.5)
    lo=bpy.data.objects.new('sun',ld);sc.collection.objects.link(lo)
    lo.rotation_euler=(math.radians(35),0,math.radians(150))   # afternoon sun from the north-west (Adelaide)
    try: sc.eevee.use_shadows=True
    except Exception: pass
    if ground:
        me=bpy.data.meshes.new('ground');bm=bmesh.new()
        R=400;vs=[bm.verts.new((R*math.cos(a),R*math.sin(a),-0.02)) for a in np.linspace(0,2*math.pi,64,endpoint=False)];bm.faces.new(vs);bm.to_mesh(me)
        g=bpy.data.objects.new('ground',me);sc.collection.objects.link(g)
        gm=bpy.data.materials.new('ground');gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.16,0.3,0.1,1)
        gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;me.materials.append(gm)
def camera_from(p,W,H,name='cam'):
    p=np.asarray(p,float);C=p[0:3];f,r,u=cam.axes(*p[3:6]);fl,cx,cy=p[6],p[7],p[8]
    cd=bpy.data.cameras.new(name);cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=fl*36/W
    cd.shift_x=(W/2-cx)/W;cd.shift_y=(cy-H/2)/W;cd.clip_start=1;cd.clip_end=3000
    ob=bpy.data.objects.new(name,cd);sc.collection.objects.link(ob)
    M=Matrix(((r[0],u[0],-f[0]),(r[1],u[1],-f[1]),(r[2],u[2],-f[2])))
    ob.matrix_world=Matrix.Translation(Vector(C))@M.to_4x4();sc.camera=ob;return ob
def look_cam(eye,target,lens=35,name='cam'):
    cd=bpy.data.cameras.new(name);cd.lens=lens;cd.clip_start=0.5;cd.clip_end=3000
    ob=bpy.data.objects.new(name,cd);sc.collection.objects.link(ob)
    ob.location=Vector(eye);d=Vector(target)-Vector(eye);ob.rotation_euler=d.to_track_quat('-Z','Y').to_euler();sc.camera=ob;return ob
def render(path):
    sc.render.filepath=path;bpy.ops.render.render(write_still=True)
if CMD=='match':
    setup_render(cam.W,cam.H,ground=True)
    camera_from(json.load(open(os.path.join(HERE,'cam.json')))['p'],cam.W,cam.H);render(OUT+'.png')
elif CMD=='matchc32':
    J=json.load(open(os.path.join(HERE,'cam_c32.json')));W,H=J['W']//2,J['H']//2;p=list(J['p']);p[6]/=2;p[7]/=2;p[8]/=2
    setup_render(W,H,ground=False);sc.render.film_transparent=True;camera_from(p,W,H);render(OUT+'.png')
elif CMD=='turn':
    setup_render(1600,900);c=Vector((-4,-2,8))
    ob=look_cam((0,0,0),c,lens=30)
    for i,az in enumerate((45,135,225,315)):
        a=math.radians(az);ob.location=(c.x+230*math.sin(a),c.y+230*math.cos(a),95)
        ob.rotation_euler=(c-ob.location).to_track_quat('-Z','Y').to_euler();render(f'{OUT}_{az:03d}.png')
elif CMD=='turnvid':
    setup_render(1280,720);c=Vector((-4,-2,8));ob=look_cam((0,0,0),c,lens=30);N=int(argv[2]) if len(argv)>2 else 120
    os.makedirs(OUT,exist_ok=True)
    for i in range(N):
        a=2*math.pi*i/N;ob.location=(c.x+230*math.sin(a),c.y+230*math.cos(a),95)
        ob.rotation_euler=(c-ob.location).to_track_quat('-Z','Y').to_euler();render(os.path.join(OUT,f'f{i:04d}.png'))
elif CMD=='close':
    setup_render(1920,1080);VIEWS=[v for v in os.environ.get('VIEWS','').split(',') if v]
    def rv(tag):
        if not VIEWS or tag in VIEWS: render(OUT+'_'+tag+'.png')
    look_cam((-12,-48,3.0),(-12,-92,6.0),lens=24,name='c1');rv('ses')
    look_cam((-30,-28,2.0),(-52,-60,5.0),lens=24,name='c2');rv('wbcc')
    look_cam((-30,10,3.0),(-60,10,5.0),lens=24,name='c3');rv('ws')
    look_cam((-14,-130,2.0),(-14,-104,6.0),lens=24,name='c4');rv('sesrear')
    look_cam((-30,70,4.0),(-50,90,3.0),lens=24,name='c5');rv('nw')
    _ia=30;_t=geo.TH[_ia]+math.radians(1.0);_r=geo.RF[_ia]
    look_cam(tuple(geo.P(_r-9,_t-math.radians(4),1.7)),tuple(geo.P(_r+3,_t,1.6)),lens=24,name='c6');rv('aisle')
    look_cam(tuple(geo.P(_r-12,math.radians(92),5.0)),tuple(geo.P(_r+4,math.radians(72),1.5)),lens=24,name='c12');rv('openterrace')
    look_cam((35,25,3.0),(63,44,2.5),lens=24,name='c7');rv('terrace')
    look_cam((-80,-58,3.0),(-62,-58,5.0),lens=24,name='c8');rv('wbccwest')
    look_cam((-56,-92,3.0),(-56,-72,5.0),lens=24,name='c9');rv('wbccsouth')
    look_cam((-40,-5,2.5),(-57,5,2.0),lens=24,name='c11');rv('wssigns')
elif CMD in ('glb','glbfield'):
    bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',export_apply=True,export_yup=True)
