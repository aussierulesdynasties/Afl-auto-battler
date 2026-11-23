import bpy, numpy as np
o = bpy.data.objects['bg_far_water']; me = o.data; a = me.color_attributes['Col']
c = np.zeros(len(a.data) * 4); a.data.foreach_get('color', c); c = c.reshape(-1, 4)[:, :3]
li = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', li)
co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)[li]
r = np.hypot(co[:, 0], co[:, 1]); s = (r > 1500) & (r < 8000) & (co[:, 1] > 0)
print('BAY n', s.sum(), 'mean', c[s].mean(0).round(4), 'std', c[s].std(0).round(4), 'p5', np.percentile(c[s], 5, 0).round(4), 'p95', np.percentile(c[s], 95, 0).round(4))
