import bpy
sc=bpy.context.scene
for n in ('ground_dirt','ground_grass','green_roof_f'):
    o=bpy.data.objects[n];print('COL',n,[c.name for c in o.users_collection],o.hide_render)
print('CAMZ',sc.camera.matrix_world.translation)
w=sc.world;print('WNODES',[(n.type,[l.to_socket.name for l in n.outputs[0].links] if n.outputs else '') for n in w.node_tree.nodes])
e=sc.eevee;print('EEVEE',[(a,getattr(e,a)) for a in ('use_gtao','use_bloom','use_volumetric_shadows','use_shadows','use_raytracing') if hasattr(e,a)])
m=bpy.data.materials['roof_green'];print('BLEND',getattr(m,'surface_render_method',None),m.use_backface_culling)
o=bpy.data.objects['green_roof_f'];me=o.data;print('NORMAL',[tuple(round(x,2) for x in (o.matrix_world.to_3x3()@p.normal)) for p in me.polygons][:4])
