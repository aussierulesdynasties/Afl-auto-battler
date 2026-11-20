# blender -b --python blend2.py -- MODE OUT     MODE: shade (white materials, for delighting) | final
import bpy,bmesh,json,math,sys,os
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
argv=sys.argv[sys.argv.index('--')+1:];MODE=argv[0];OUT=argv[1];TT=('tt' in argv)
HERE=os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
P=json.load(open('model2.json'));p=json.load(open('cam.json'))['p']
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
W,H=800,581;RS=2
C=Vector(p[:3]);yaw,pit,roll=p[3:6]
fw=Vector((math.cos(yaw)*math.cos(pit),math.sin(yaw)*math.cos(pit),math.sin(pit)));rt=Vector((math.sin(yaw),-math.cos(yaw),0));up=rt.cross(fw)
cr,sr=math.cos(roll),math.sin(roll);R0=cr*rt+sr*up;U0=-sr*rt+cr*up
def proj(X):
    d=X-C;x=d.dot(R0);y=d.dot(U0);z=d.dot(fw);return (p[7]+p[6]*x/z, p[8]-p[6]*y/z)
# material key -> (detail texture, tile metres, normal map or None, fallback colour sRGB 0-255)
D='det/';N='ph/'
MK={
 'roof_rust':('rusty_corrugated_iron',2.0,'rusty_corrugated_iron',(150,80,60)),
 'roof_white':('box_profile_metal_sheet',2.0,'box_profile_metal_sheet',(235,235,230)),
 'roof_under':('corrugated_iron_03',2.0,'corrugated_iron_03',(70,72,70)),
 'roof_grey':('corrugated_iron_03',2.0,'corrugated_iron_03',(170,175,178)),
 'roof_terracotta':('corrugated_iron_03',2.0,'corrugated_iron_03',(190,110,90)),
 'fascia':('concrete_floor_worn_001',3.0,None,(220,220,215)),
 'ejs_tread':('concrete_floor_worn_001',3.0,'concrete_floor_worn_001',(185,180,170)),
 'ejs_riser':('concrete_floor_worn_001',3.0,'concrete_floor_worn_001',(175,170,160)),
 'ejs_inwall':('concrete_floor_worn_001',3.0,None,(225,225,220)),
 'ejs_outwall':('concrete_floor_worn_001',3.0,'concrete_floor_worn_001',(165,155,145)),
 'steel_blue':('metal_plate_02',2.0,None,(85,95,118)),
 'steel_white':('metal_plate_02',2.0,None,(220,220,215)),
 'steel_grey':('metal_plate_02',2.0,None,(140,140,140)),
 'pole':('metal_plate_02',2.0,None,(205,205,200)),
 'lamp':('metal_plate_02',2.0,None,(60,60,60)),
 'brick_wall':('brick_wall_001',3.0,'brick_wall_001',(200,125,100)),
 'render_white':('concrete_floor_worn_001',3.0,None,(235,232,225)),
 'concrete_flat':('concrete_floor_worn_001',3.0,'concrete_floor_worn_001',(185,180,172)),
 'ring_tread':('concrete_floor_worn_001',3.0,'concrete_floor_worn_001',(150,148,145)),
 'ring_riser':('concrete_floor_worn_001',3.0,'concrete_floor_worn_001',(130,128,125)),
 'bank_tread':('concrete_floor_worn_001',3.0,'concrete_floor_worn_001',(170,165,158)),
 'bank_riser':('concrete_floor_worn_001',3.0,'concrete_floor_worn_001',(150,145,138)),
 'bank_earth':('dry_ground_01',3.0,'dry_ground_01',(175,160,140)),
 'scoreboard_face':('metal_plate_02',2.0,None,(35,38,40)),
 'adwall':('concrete_floor_worn_001',3.0,None,(240,238,230)),
 'scoreboard':('concrete_floor_worn_001',3.0,None,(230,228,220)),
 'sign':('metal_plate_02',2.0,None,(200,40,40)),
 'seat_tread':('concrete_floor_worn_001',3.0,'concrete_floor_worn_001',(120,126,134)),
 'seat_riser':('concrete_floor_worn_001',3.0,'concrete_floor_worn_001',(100,104,110)),
 'bench':('bench',1.5,None,(150,150,150)),
 'aisle':('concrete_floor_worn_001',3.0,'concrete_floor_worn_001',(215,215,210)),
 'ejw_back':('concrete_floor_worn_001',3.0,None,(235,225,210)),
 'ejw_fascia':('concrete_floor_worn_001',3.0,None,(238,232,220)),
 'red_panel':('box_profile_metal_sheet',2.0,'box_profile_metal_sheet',(190,110,90)),
 'apron':('asphalt_02',3.0,'asphalt_02',(190,186,178)),
 'turf':(None,1,None,(92,120,70)),
}
def lin(c):c=c/255;return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
# ---------- build meshes ----------
objs=[]
for name,pt in P.items():
    if name=='inside_turf_removable' and not TT:continue
    me=bpy.data.meshes.new(name);me.from_pydata([tuple(v) for v in pt['v']],[],[tuple(f) for f in pt['f']]);me.update()
    ob=bpy.data.objects.new(name,me);sc.collection.objects.link(ob);objs.append(ob)
    keys=sorted(set(pt['m']))
    bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table()
    lay=bm.faces.layers.int.new('mk')
    for f,m in zip(bm.faces,pt['m']):f[lay]=keys.index(m)
    for it in range(6):  # split long edges so visibility is decided on pieces of at most ~3 m
        long=[e for e in bm.edges if e.calc_length()>3.0]
        if not long:break
        bmesh.ops.subdivide_edges(bm,edges=long,cuts=1,use_grid_fill=True)
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=0.001)
    bm.to_mesh(me);bm.free();ob['keys']=json.dumps(keys);ob['o']=pt['o'];ob['a']=pt['a']
bpy.context.view_layer.update()
# BVH of the whole scene (world == local, no transforms)
allv=[];allf=[];own=[]
for ob in objs:
    k=len(allv);allv+= [v.co.copy() for v in ob.data.vertices]
    for pl in ob.data.polygons:allf.append([k+i for i in pl.vertices]);own.append((ob.name,pl.index))
bvh=BVHTree.FromPolygons(allv,allf)
TH=0.45
THIN=('turf','steel_blue','steel_white','steel_grey','pole','lamp')
stats={};VIS={}
for ob in objs:
    me=ob.data;keys=json.loads(ob['keys']);o=Vector((*ob['o'],0));a=Vector((*ob['a'],0)).normalized();aperp=Vector((-a.y,a.x,0))
    uvt=me.uv_layers.new(name='tex');uvp=me.uv_layers.new(name='proj')
    mk_attr=me.attributes['mk'].data
    slot={}
    for pl in me.polygons:
        n=pl.normal;cen=pl.center;dv=(C-cen);dist=dv.length;dv.normalize()
        hit=bvh.ray_cast(C,(cen-C).normalized(),dist+1)
        vis=hit[0] is not None and (hit[0]-cen).length<0.08
        fac=abs(n.dot(dv));key=keys[mk_attr[pl.index].value];VIS[(ob.name,pl.index)]=vis
        mode='T'
        nm=key+'_'+mode;stats[nm]=stats.get(nm,0)+1
        if nm not in slot:slot[nm]=len(slot);me.materials.append(bpy.data.materials.get(nm) or bpy.data.materials.new(nm))
        pl.material_index=slot[nm]
        horiz=abs(n.z)>0.6
        if not horiz:t=Vector((0,0,1)).cross(n);t=t.normalized() if t.length>1e-6 else a
        for li in pl.loop_indices:
            X=me.vertices[me.loops[li].vertex_index].co;q=X-o
            if horiz:uvt.data[li].uv=(q.dot(a),q.dot(aperp))
            else:uvt.data[li].uv=(q.dot(t),X.z)
            u,v=proj(X);uvp.data[li].uv=(u/W,1-v/H)
    for pl in me.polygons:pl.use_smooth=False
print('FACES',json.dumps(stats))
# ---------- hand-made procedural materials (no photo pixels) ----------
# STYLE: key -> (pattern, base sRGB 0-255, roughness). Colours read by eye from the period photos.
STYLE={
 'roof_rust':('corrugated',(150,78,55),0.7),'roof_white':('boxprofile',(232,232,228),0.45),'roof_under':('corrugated',(105,108,108),0.7),
 'roof_grey':('corrugated',(172,176,178),0.55),'roof_terracotta':('tiles',(178,92,66),0.75),'ejwseat_tread':('concrete',(150,150,146),0.9),'ejwseat_riser':('concrete',(126,126,122),0.9),'ejwseat_bench':('paint',(62,98,160),0.5),'navy_wall':('paint',(52,70,84),0.6),'roof_pink':('paint',(214,176,156),0.7),'render_pink':('render',(214,176,156),0.85),
 'fascia':('paint',(222,222,216),0.6),'ejw_fascia':('paint',(238,232,220),0.6),'ejw_back':('render',(232,224,210),0.8),
 'ejs_tread':('steps',(178,174,166),0.9),'ejs_riser':('concrete',(168,164,156),0.9),'ejs_inwall':('render',(226,226,220),0.85),
 'ejs_outwall':('concrete_panels',(170,162,150),0.9),
 'steel_blue':('paint',(85,95,118),0.5),'steel_white':('paint',(222,222,216),0.5),'steel_grey':('paint',(140,140,140),0.55),
 'pole':('galv',(196,198,198),0.45),'lamp':('paint',(55,57,60),0.5),
 'brick_wall':('brick',(160,82,58),0.9),'render_white':('render',(236,233,226),0.85),'concrete_flat':('concrete',(186,181,172),0.9),
 'ring_tread':('steps',(160,157,152),0.9),'ring_riser':('concrete',(140,138,134),0.9),
 'bank_tread':('steps',(176,170,160),0.9),'bank_riser':('concrete',(160,154,144),0.9),'bank_earth':('dirt',(176,168,156),1.0),
 'adwall':('paint',(240,238,232),0.6),'scoreboard':('render',(230,228,220),0.8),'scoreboard_face':('board',(26,28,30),0.6),
 'sign':('paint',(200,32,38),0.4),'ad_orange':('paint',(226,104,40),0.5),'ad_yellow':('paint',(196,190,96),0.5),'ad_navy':('paint',(50,62,110),0.5),'ad_cream':('paint',(226,214,140),0.5),'opening':('paint',(30,32,34),0.95),'door':('timber',(78,92,80),0.7),'window':('paint',(50,60,68),0.25),
 'seat_tread':('steps',(128,138,146),0.9),'seat_riser':('concrete',(104,112,120),0.9),'bench':('paint',(140,152,156),0.6),
 'aisle':('paint',(190,190,185),0.8),'red_panel':('boxprofile',(165,58,48),0.55),'apron':('worn_asphalt',(166,157,146),0.92),'fence_white':('paint',(232,230,222),0.6),'fence_cap':('concrete',(214,210,200),0.8),'kerb':('concrete',(184,178,166),0.9),'drain':('grate',(70,70,68),0.5),
 'turf':('grass',(92,120,70),1.0),
 'court_clay':('clay',(170,92,74),0.95),'court_line':('paint',(222,212,202),0.7),'net':('paint',(38,40,38),0.8),'windbreak':('paint',(50,88,70),0.9),
 'roof_green':('corrugated',(196,204,160),0.6),'render_cream':('render',(228,222,198),0.85),'grass_patch':('grass',(116,134,80),1.0),'dirt_apron':('dirt',(190,166,138),1.0),
 'palm_trunk':('timber',(126,110,90),0.9),'palm_frond':('grass',(76,104,58),0.8),'leaf':('grass',(68,94,52),0.9),'shrub':('grass',(62,80,48),0.9),'bark':('timber',(96,80,64),0.9),'rubble':('stones',(168,160,146),0.95),
}
def build_mat(m,key):
    pat,base,rough=STYLE[key]
    m.use_nodes=True;nt=m.node_tree;ns=nt.nodes;L=nt.links.new;bs=ns['Principled BSDF']
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=0.0;m.use_backface_culling=False
    if MODE=='shade':
        bs.inputs['Base Color'].default_value=(0.8,0.8,0.8,1);return
    bc=[lin(x) for x in base]
    uv=ns.new('ShaderNodeUVMap');uv.uv_map='tex';sep=ns.new('ShaderNodeSeparateXYZ');L(uv.outputs[0],sep.inputs[0])
    def rgbn(col):
        r=ns.new('ShaderNodeRGB');r.outputs[0].default_value=(*col,1);return r.outputs[0]
    def mth(op,a,b=None,c=None):
        n=ns.new('ShaderNodeMath');n.operation=op
        for i,x in enumerate((a,b,c)):
            if x is None:continue
            if isinstance(x,(int,float)):n.inputs[i].default_value=x
            else:L(x,n.inputs[i])
        return n.outputs[0]
    def mix(fac,a,b):
        n=ns.new('ShaderNodeMix');n.data_type='RGBA';n.blend_type='MIX'
        if isinstance(fac,(int,float)):n.inputs['Factor'].default_value=fac
        else:L(fac,n.inputs['Factor'])
        L(a,n.inputs[6]);L(b,n.inputs[7]);return n.outputs[2]
    def noise(scale,detail=4,vec=None):
        n=ns.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=detail;n.inputs['Roughness'].default_value=0.55
        L(vec or uv.outputs[0],n.inputs['Vector']);return n.outputs['Fac']
    def shade(col,k):
        h=ns.new('ShaderNodeMix');h.data_type='RGBA';h.blend_type='MULTIPLY';h.inputs['Factor'].default_value=1.0
        cc=ns.new('ShaderNodeCombineXYZ')
        for i in range(3):
            if isinstance(k,(int,float)):cc.inputs[i].default_value=k
            else:L(k,cc.inputs[i])
        L(col,h.inputs[6]);L(cc.outputs[0],h.inputs[7]);return h.outputs[2]
    def vary(col,amp,scale):
        return shade(col,mth('ADD',mth('MULTIPLY',noise(scale),amp),1-amp/2))
    def scaled(sx,sy):
        mp=ns.new('ShaderNodeMapping');mp.inputs['Scale'].default_value=(sx,sy,1);L(uv.outputs[0],mp.inputs[0]);return mp.outputs[0]
    def frac_u(pitch):return mth('FRACT',mth('DIVIDE',sep.outputs[0],pitch))
    def joint(axis,pitch,w):
        return mth('LESS_THAN',mth('FRACT',mth('DIVIDE',sep.outputs[axis],pitch)),w)
    col=rgbn(bc);height=None
    if pat=='corrugated':  # 76 mm sine corrugation across u, streaky weathering along the fall
        height=mth('MULTIPLY',mth('ADD',mth('SINE',mth('MULTIPLY',frac_u(0.076),6.28318)),1.0),0.5)
        col=vary(col,0.03,0.6)
        col=shade(col,mth('ADD',mth('MULTIPLY',noise(3.0,6,scaled(4.0,0.25)),0.06),0.97))
    elif pat=='boxprofile':  # trapezoid ribs every 200 mm
        height=mth('LESS_THAN',frac_u(0.2),0.25);col=vary(col,0.06,0.8)
    elif pat=='tiles':
        height=mth('MULTIPLY',mth('ADD',mth('SINE',mth('MULTIPLY',frac_u(0.25),6.28318)),1.0),mth('FRACT',mth('DIVIDE',sep.outputs[1],0.35)))
        col=vary(col,0.15,2.0)
    elif pat in('concrete','render','paint','galv'):
        amp={'concrete':0.03,'render':0.02,'paint':0.015,'galv':0.03}[pat]
        col=vary(col,amp,{'concrete':2.5,'render':1.2,'paint':0.8,'galv':3.0}[pat])
        if pat=='concrete':col=vary(col,0.05,18.0)
    elif pat=='concrete_panels':  # precast panels, a joint at every pier (4.55 m)
        col=vary(col,0.03,2.0);col=mix(joint(0,4.55,0.006),col,rgbn([x*0.55 for x in bc]))
    elif pat=='steps':  # cast concrete, a joint every 3 m
        col=vary(col,0.03,2.0);col=vary(col,0.05,22.0);col=mix(joint(0,3.0,0.004),col,rgbn([x*0.6 for x in bc]))
    elif pat=='brick':
        br=ns.new('ShaderNodeTexBrick');L(uv.outputs[0],br.inputs['Vector']);br.inputs['Scale'].default_value=1.0
        br.inputs['Brick Width'].default_value=0.23;br.inputs['Row Height'].default_value=0.076;br.inputs['Mortar Size'].default_value=0.01
        br.inputs['Color1'].default_value=(*bc,1);br.inputs['Color2'].default_value=(*[x*0.8 for x in bc],1)
        br.inputs['Mortar'].default_value=(*[lin(x) for x in (196,186,170)],1);br.offset=0.5;br.squash_frequency=1
        col=vary(br.outputs['Color'],0.1,6.0);height=mth('SUBTRACT',1.0,br.outputs['Fac'])
    elif pat=='timber':  # weathered planks, grain along u
        col=shade(col,mth('ADD',mth('MULTIPLY',noise(2.0,8,scaled(0.6,30.0)),0.35),0.82))
    elif pat=='dirt':
        col=vary(col,0.04,1.2);col=vary(col,0.08,12.0)
        mr=ns.new('ShaderNodeMapRange');mr.interpolation_type='SMOOTHSTEP';mr.inputs['From Min'].default_value=0.55;mr.inputs['From Max'].default_value=0.7;L(noise(0.8,3),mr.inputs['Value']);pass
    elif pat=='asphalt':
        col=vary(col,0.1,1.0);col=vary(col,0.18,60.0)
    elif pat=='board':  # black panels in a grid with grey frames
        col=mix(mth('MAXIMUM',joint(0,1.0,0.05),joint(1,0.6,0.08)),col,rgbn([lin(x) for x in (70,72,74)]))
    elif pat=='clay':  # en-tout-cas court: fine crushed brick, faint wear
        col=vary(col,0.1,1.5);col=vary(col,0.06,30.0)
    elif pat=='stones':  # rock pitching: irregular stones, each its own shade, dark joints
        vo=ns.new('ShaderNodeTexVoronoi');vo.inputs['Scale'].default_value=2.4;L(uv.outputs[0],vo.inputs['Vector'])
        ve=ns.new('ShaderNodeTexVoronoi');ve.feature='DISTANCE_TO_EDGE';ve.inputs['Scale'].default_value=2.4;L(uv.outputs[0],ve.inputs['Vector'])
        col=shade(col,mth('ADD',mth('MULTIPLY',vo.outputs['Color'],0.35),0.78));col=vary(col,0.08,20.0)
        edge=mth('LESS_THAN',ve.outputs['Distance'],0.05);col=mix(edge,col,rgbn([x*0.45 for x in bc]));height=mth('SUBTRACT',1.0,edge)
    elif pat=='worn_asphalt':  # hand-made: warm grey-brown seal, broad patchy wear, worn lighter tracks, patched darker
        col=vary(col,0.02,0.18);col=vary(col,0.02,1.5)
        mr=ns.new('ShaderNodeMapRange');mr.interpolation_type='SMOOTHSTEP';mr.inputs['From Min'].default_value=0.58;mr.inputs['From Max'].default_value=0.66;L(noise(0.12,3),mr.inputs['Value'])
        col=mix(mth('MULTIPLY',mr.outputs['Result'],0.0),col,rgbn([lin(x) for x in (124,116,106)]))  # patched / oil-dark areas
        mw=ns.new('ShaderNodeMapRange');mw.interpolation_type='SMOOTHSTEP';mw.inputs['From Min'].default_value=0.6;mw.inputs['From Max'].default_value=0.72;L(noise(0.25,2,scaled(0.35,1.0)),mw.inputs['Value'])
        col=mix(mth('MULTIPLY',mw.outputs['Result'],0.0),col,rgbn([lin(x) for x in (190,182,170)]))  # worn pale tracks
        ag=ns.new('ShaderNodeTexVoronoi');ag.inputs['Scale'].default_value=22.0;L(uv.outputs[0],ag.inputs['Vector'])  # gravel aggregate ~2 cm
        col=shade(col,mth('ADD',mth('MULTIPLY',ag.outputs['Color'],0.55),0.74));col=vary(col,0.03,6.0);col=vary(col,0.10,90.0)
        ck=ns.new('ShaderNodeTexVoronoi');ck.feature='DISTANCE_TO_EDGE';ck.inputs['Scale'].default_value=0.6;L(noise(0.9,2,None) if False else uv.outputs[0],ck.inputs['Vector'])
        crack=mth('MULTIPLY',mth('LESS_THAN',ck.outputs['Distance'],0.005),mth('GREATER_THAN',noise(0.35,2),0.72))  # a few fine hairline cracks only
        col=mix(mth('MULTIPLY',crack,0.6),col,rgbn([lin(x) for x in (104,98,90)]))
        height=mth('SUBTRACT',mth('MULTIPLY',ag.outputs['Distance'],1.0),crack)
    elif pat=='grate':  # steel grate: bars every 40 mm in a frame
        col=mix(mth('LESS_THAN',frac_u(0.04),0.45),col,rgbn([lin(x) for x in (24,24,24)]));height=mth('LESS_THAN',frac_u(0.04),0.45)
    elif pat=='grass':
        col=vary(col,0.04,3.0);col=vary(col,0.10,60.0)
    L(col,bs.inputs['Base Color'])
    if height is not None:
        bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=0.6;bump.inputs['Distance'].default_value=0.02
        L(height,bump.inputs['Height']);L(bump.outputs[0],bs.inputs['Normal'])
for m in bpy.data.materials:
    build_mat(m,m.name.rsplit('_',1)[0])
# ---------- camera, light ----------
cd=bpy.data.cameras.new('cam');cam=bpy.data.objects.new('cam',cd);sc.collection.objects.link(cam);sc.camera=cam
cam.matrix_world=Matrix.Translation(C)@Matrix((R0,U0,-fw)).transposed().to_4x4()
cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=p[6]*36/W;cd.shift_x=(W/2-p[7])/W;cd.shift_y=(p[8]-H/2)/W;cd.clip_end=5000
sc.render.resolution_x=W*RS;sc.render.resolution_y=H*RS;sc.render.film_transparent=True
sc.render.engine='CYCLES';sc.cycles.samples=64;sc.cycles.use_denoising=True;sc.cycles.device='CPU'
sd=bpy.data.lights.new('sun','SUN');sd.energy=5.0;sd.angle=math.radians(1);sun=bpy.data.objects.new('sun',sd);sc.collection.objects.link(sun)
az=math.radians(105);el=math.radians(38);dirv=Vector((math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el)))
sun.rotation_euler=(-dirv).to_track_quat('-Z','Y').to_euler()
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[1].default_value=0.22
w.node_tree.nodes['Background'].inputs[0].default_value=(0.75,0.8,0.9,1)
sc.view_settings.view_transform='Standard'
if not TT:
    if MODE=='shade':
        sc.render.image_settings.file_format='OPEN_EXR';sc.render.image_settings.color_depth='32';sc.render.filepath=os.path.abspath(OUT+'_shade.exr')
    else:sc.render.filepath=os.path.abspath(OUT+'_matched.png')
    bpy.ops.render.render(write_still=True)
if MODE=='final':
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT+'.blend'))
