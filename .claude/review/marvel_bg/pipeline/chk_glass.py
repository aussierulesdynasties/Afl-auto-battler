import bpy
o = bpy.data.objects['bg_bld_tower_glass_navy_a']; v = o.data.vertices
xs=[p.co.x for p in v]; ys=[p.co.y for p in v]; zs=[p.co.z for p in v]
print('BB', min(xs),max(xs),min(ys),max(ys),min(zs),max(zs))
uv=o.data.uv_layers[0].data; us=[d.uv.x for d in uv]; vs=[d.uv.y for d in uv]; print('UV', min(us),max(us),min(vs),max(vs))
m=o.data.materials[0]; im=[n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE'][0]; print('IM', im.name, im.alpha_mode, im.colorspace_settings.name)
c=o.data.color_attributes['Col'].data; print('COL', list(c[0].color))
p=o.data.polygons[0]; print('C0', tuple(p.center), tuple(p.normal))
