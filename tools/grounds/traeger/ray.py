import bpy
from bpy_extras.view3d_utils import region_2d_to_vector_3d
sc=bpy.context.scene;cam=sc.camera;dg=bpy.context.evaluated_depsgraph_get()
W,H=sc.render.resolution_x,sc.render.resolution_y
fr=cam.data.view_frame(scene=sc);mw=cam.matrix_world
for px,py in [(1175,344),(1120,335),(1230,350)]:
    u=px/W;v=1-py/H
    tl,tr,br,bl=fr[3],fr[0],fr[1],fr[2]  # view_frame order: tr,br,bl,tl
    p=bl+(br-bl)*u+(tl-bl)*v
    o=mw.translation;d=(mw@p-o).normalized();org=o.copy()
    for i in range(5):
        hit,loc,n,idx,ob,_=sc.ray_cast(dg,org,d)
        if not hit:break
        m=ob.material_slots[ob.data.polygons[idx].material_index].material.name if ob.material_slots else None
        print('HIT',px,py,i,ob.name,m,round((loc-o).length,1));org=loc+d*0.01
