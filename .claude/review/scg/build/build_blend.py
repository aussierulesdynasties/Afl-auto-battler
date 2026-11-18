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
MI={('ph',k):mat('photo%d'%k,tex='photo%d.png'%k) for k in range(D.get('NPH',1))}
for k,c in D['MATS'].items():MI[k]=mat(k,col=c,rough=0.3 if k in('glass','glassd','screen','lamp') else 0.85)
bm=bmesh.new();vs=[bm.verts.new(v) for v in D['V']];uvl=bm.loops.layers.uv.new('UV')
PC=Vector((0.94,-11.82,0))
for f in D['F']:
    try:fa=bm.faces.new([vs[i] for i in f['v']])
    except ValueError:continue
    if f['uv'] is not None:
        fa.material_index=MI[('ph',f.get('ph',0))]
        for l,uv in zip(fa.loops,f['uv']):l[uvl].uv=uv
    else:
        fa.material_index=MI[f['m']]
        for l in fa.loops:
            p=l.vert.co;a=math.atan2(p.y-PC.y,p.x-PC.x);r=(Vector((p.x,p.y,0))-PC).length
            if f['m'] in('facade','brick'):l[uvl].uv=(a*r/(27.0 if f['m']=='facade' else 10.0),p.z/(21.0 if f['m']=='facade' else 13.0))
            else:l[uvl].uv=(a*r/40.0,r/8.0)
bm.normal_update();bm.to_mesh(me);me.update()
# GLB in metres, Godot Y-up handled by exporter
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUTGLB,export_format='GLB',use_selection=True,export_yup=True)
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
sun=bpy.data.lights.new('sun','SUN');sun.energy=3.0;so=bpy.data.objects.new('sun',sun);sc.collection.objects.link(so);so.rotation_euler=(math.radians(40),0,math.radians(-60))
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Strength'].default_value=1.0;w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.8,0.85,0.9,1)
sc.view_settings.view_transform='Standard'
sc.render.filepath=REND;bpy.ops.render.render(write_still=True)
print('DONE',len(me.polygons))
