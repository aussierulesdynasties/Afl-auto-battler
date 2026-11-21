# blender -b out/r4/traeger.blend --python options.py -- OUTDIR
# Boundary-board choice: the same two fence close-ups rendered A (all boards), B (TIO run only), C (bare fence).
import bpy,bmesh,sys,os,json,math
from mathutils import Vector
OUT=sys.argv[sys.argv.index('--')+1];HERE=os.path.abspath(os.path.join(OUT,'..','..'))
P={p['name']:p['pts'] for p in json.load(open(os.path.join(HERE,'prims.json'))) if p['name'].startswith('fence_hoard')}
C=Vector((0,5))
def oriented(pts):   # order the run so u reads left-to-right for someone on the field facing the fence
    v=[Vector(p) for p in pts];a,b=v[0],v[-1];m=v[len(v)//2]
    out=(m-C).normalized();right=Vector((out.y,-out.x))
    return v if (b-a).dot(right)>0 else v[::-1]
def arc(v):
    s=[0.0]
    for i in range(1,len(v)):s.append(s[-1]+(v[i]-v[i-1]).length)
    return s
def at(v,S,t):
    for i in range(1,len(v)):
        if S[i]>=t:f=(t-S[i-1])/max(S[i]-S[i-1],1e-6);return v[i-1].lerp(v[i],f)
    return v[-1]
def board(name,pts,img,s0,L):
    v=oriented(pts);S=arc(v);bm=bmesh.new();uv=bm.loops.layers.uv.new('UV');step=1.0;t=s0
    while t<s0+L-1e-6:
        t1=min(t+step,s0+L);a,b=at(v,S,t),at(v,S,t1)
        n=(((a+b)/2)-C).normalized()*-0.06          # 6 cm proud of the fence, field side
        q=[bm.verts.new((a.x+n.x,a.y+n.y,0.05)),bm.verts.new((b.x+n.x,b.y+n.y,0.05)),bm.verts.new((b.x+n.x,b.y+n.y,0.95)),bm.verts.new((a.x+n.x,a.y+n.y,0.95))]
        f=bm.faces.new(q);u0,u1=(t-s0)/L,(t1-s0)/L
        for l,c in zip(f.loops,((u0,0),(u1,0),(u1,1),(u0,1))):l[uv].uv=c
        t=t1
    me=bpy.data.meshes.new(name);bm.to_mesh(me);ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob)
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=0.7
    tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(img);nt.links.new(tx.outputs['Color'],bs.inputs['Base Color']);nt.links.new(tx.outputs['Alpha'],bs.inputs['Alpha'])
    me.materials.append(m);return ob
O=os.path.join(HERE,'out','opt')
vb=oriented(P['fence_hoard_blue']);tio=board('opt_tio',P['fence_hoard_blue'],os.path.join(O,'tio_run.png'),0,min(45,arc(vb)[-1]))
spn=board('opt_sponsors',P['fence_hoard'],os.path.join(O,'sponsors.png'),18,60)
vh=oriented(P['fence_hoard']);Sh=arc(vh)
def look(t,back,z=2.2):   # eye 'back' metres in from arc point t of fence_hoard, looking at the fence
    p=at(vh,Sh,t);n=(C-p).normalized();return (p.x+n.x*back,p.y+n.y*back,z),(p.x,p.y,0.6)
shots=[('north',)+look(11,15,1.8)+(18,),('far',)+look(66,15,1.8)+(22,)]
sc=bpy.context.scene;sc.render.film_transparent=False;cam=sc.camera
es=bpy.data.objects.get('east_shelter')
if es:es.hide_render=True   # the floating east slab is an open question; kept out of this board
sc.render.resolution_x=1500;sc.render.resolution_y=640
g=bpy.data.collections.get('ground')
for o in (g.objects if g else []):o.hide_render=False
for opt,vis in (('A',(1,1)),('B',(1,0)),('C',(0,0))):
    tio.hide_render=not vis[0];spn.hide_render=not vis[1]
    for n,eye,tg,lens in shots:
        cam.location=Vector(eye);cam.rotation_euler=(Vector(tg)-Vector(eye)).to_track_quat('-Z','Y').to_euler()
        cam.data.lens=lens;cam.data.sensor_width=36;cam.data.shift_x=cam.data.shift_y=0;cam.data.clip_start=0.1
        sc.render.filepath=os.path.join(OUT,'%s_%s.png'%(opt,n));bpy.ops.render.render(write_still=True);print('OK',opt,n)
