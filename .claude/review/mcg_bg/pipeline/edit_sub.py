f='scene.py'; s=open(f,newline='').read()
a="""        bm = bmesh.new(); bm.from_mesh(o.data); M = o.matrix_world
        kill = []"""
assert a in s
s=s.replace(a,"""        bm = bmesh.new(); bm.from_mesh(o.data); M = o.matrix_world
        for _ in range(12):   # split long fan triangles (UVs interpolate) so the cut follows the mask, not a face centre
            long_ = [e for e in bm.edges if (M @ e.verts[0].co - M @ e.verts[1].co).length > 3.0]
            if not long_: break
            bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False)
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
        kill = []""",1)
open(f,'w',newline='').write(s); print('ok')
