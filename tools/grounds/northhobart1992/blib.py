# Blender helpers: hand-made texture materials and an addobj() that builds a mesh from (verts, material) faces
# with real-scale UVs (u horizontal along the face, v up/down-slope, divided by the texture's real size).
import bpy,bmesh,json,math,os
from mathutils import Vector,Matrix
NH=os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else NH
SIZES=json.load(open(os.path.join(NH,'tex','sizes.json')))
SIZES['seats_top']=SIZES['concrete']
_mats={}
def TM(name):
    if name in _mats:return _mats[name]
    m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=False
    b=m.node_tree.nodes['Principled BSDF'];b.inputs['Roughness'].default_value=0.55 if name in('roof_iron','post_maroon','fascia','clock') else 0.9
    if name=='roof_iron':b.inputs['Metallic'].default_value=0.25
    fn=os.path.join(NH,'tex',('concrete' if name=='seats_top' else name)+'.png')
    t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(fn,check_existing=True);t.interpolation='Cubic'
    m.node_tree.links.new(t.outputs[0],b.inputs['Base Color']);_mats[name]=m;return m
def addobj(name,faces,dissolve=False,steep=None,uvfit=False,double=False,coll=None):
    bm=bmesh.new();uvl=bm.loops.layers.uv.new();names=[]
    for vs,mat in faces:
        V=[Vector(v) for v in vs]
        n=(V[1]-V[0]).cross(V[2]-V[0])
        if n.length<1e-9:continue
        n.normalize()
        if steep and abs(n.z)<0.25:mat=steep
        if mat not in names:names.append(mat)
        try:f=bm.faces.new([bm.verts.new(v) for v in V])
        except ValueError:continue
        f.material_index=names.index(mat)
        su,sv=SIZES.get(mat,(1,1))
        h=Vector((-n.y,n.x,0))
        ud=h.normalized() if h.length>0.05 else Vector((1,0,0))
        vd=n.cross(ud)
        if uvfit:
            for k,l in enumerate(f.loops):l[uvl].uv=[(0,0),(1,0),(1,1),(0,1)][k]
        else:
            for l in f.loops:p=l.vert.co;l[uvl].uv=(p.dot(ud)/su,p.dot(vd)/sv)
    bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-4)
    if dissolve:
        bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(0.5),verts=bm.verts[:],edges=bm.edges[:],delimit={'MATERIAL','UV'})
        bmesh.ops.triangulate(bm,faces=bm.faces[:])
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);(coll or bpy.context.scene.collection).objects.link(o)
    for m in names:o.data.materials.append(TM(m))
    for p in o.data.polygons:p.use_smooth=False
    return o
def addgrid(name,G,mat,steep=None,flip=False,dz=0.0):
    # G: list of columns, each a list of (x,y,z); shared vertices, planar regions dissolved after UVs are set
    bm=bmesh.new();uvl=bm.loops.layers.uv.new();nc,nr=len(G),len(G[0])
    V=[[bm.verts.new((p[0],p[1],p[2]+dz)) for p in col] for col in G]
    names=[mat]+([steep] if steep else [])
    for i in range(nc-1):
        for j in range(nr-1):
            for tri in (((i,j),(i+1,j),(i+1,j+1)),((i,j),(i+1,j+1),(i,j+1))):
                vs=[V[a][b] for a,b in tri]
                if flip:vs=vs[::-1]
                if len(set(vs))<3:continue
                n=(vs[1].co-vs[0].co).cross(vs[2].co-vs[0].co)
                if n.length<1e-10:continue
                try:f=bm.faces.new(vs)
                except ValueError:continue
                n.normalize();m=steep if (steep and abs(n.z)<0.25) else mat;f.material_index=names.index(m)
                su,sv=SIZES.get(m,(1,1));h=Vector((-n.y,n.x,0));ud=h.normalized() if h.length>0.05 else Vector((1,0,0));vd=n.cross(ud)
                for l in f.loops:p=l.vert.co;l[uvl].uv=(p.dot(ud)/su,p.dot(vd)/sv)
    bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(0.5),verts=bm.verts[:],edges=bm.edges[:],delimit={'MATERIAL','UV'})
    bmesh.ops.triangulate(bm,faces=bm.faces[:])
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o)
    for m in names:o.data.materials.append(TM(m))
    for p in o.data.polygons:p.use_smooth=False
    return o
