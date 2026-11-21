# The outer grass apron as a ring: the site rectangle with the boundary-fence shape cut out, so the model has no
# playing field of its own (director 2026-11-18: "Leave field out"); the game draws its grass inside the fence.
import bpy,bmesh
def ring_mesh(me,outer,inner,z,tile):
    bm=bmesh.new()
    for loop in (outer,inner):
        vs=[bm.verts.new((x,y,z)) for x,y in loop]
        for i in range(len(vs)):bm.edges.new((vs[i],vs[(i+1)%len(vs)]))
    bmesh.ops.triangle_fill(bm,use_beauty=True,use_dissolve=False,edges=bm.edges[:])
    for f in bm.faces:
        if f.normal.z<0:f.normal_flip()
    ul=bm.loops.layers.uv.new('UV')
    for f in bm.faces:
        for l in f.loops:l[ul].uv=(l.vert.co.x/tile[0],l.vert.co.y/tile[1])
    area=sum(f.calc_area() for f in bm.faces);bm.to_mesh(me);bm.free();me.update();return area
