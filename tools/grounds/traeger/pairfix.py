# A single quad has no inside, so recalc_face_normals picks its side at random. For every top face with an
# underside twin (name + '_u'), point the top face up and the underside down, so the right one shows from above.
import bpy,bmesh
def pair_fix(objs):
    names={o.name:o for o in objs};n=0
    for o in objs:
        u=names.get(o.name+'_u')
        if not u:continue
        for ob,want_up in ((o,True),(u,False)):
            me=ob.data;z=sum((ob.matrix_world.to_3x3()@p.normal).z*p.area for p in me.polygons)
            if (z>0)!=want_up:
                bm=bmesh.new();bm.from_mesh(me);bmesh.ops.reverse_faces(bm,faces=bm.faces[:]);bm.to_mesh(me);bm.free();me.update();n+=1
    return n
