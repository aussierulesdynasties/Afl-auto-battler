"""Quay wall: plain concrete, not the window facade texture. Water: real IOR 1.33, near-mirror roughness."""
P = 'scene.py'; s = open(P, newline='').read()
a = "mat_img('quay', os.path.join(HERE, 'tex', 'wall.png'), 0.9)"; assert s.count(a) == 1
s = s.replace(a, "mat_quay()")
b = "    wob = mk_obj('bg_water', wv, wf, wmat)"; assert s.count(b) == 1
s = s.replace(b, "    _wb.inputs['IOR'].default_value = 1.33; _wb.inputs['Roughness'].default_value = 0.03   # water: real IOR, near-mirror\n"
              "    def mat_quay():\n"
              "        m = bpy.data.materials.new('quay'); m.use_nodes = True; bb = m.node_tree.nodes['Principled BSDF']\n"
              "        bb.inputs['Base Color'].default_value = (*lin((118, 114, 106)), 1); bb.inputs['Roughness'].default_value = 0.9; return m\n" + b)
open(P, 'w', newline='').write(s); print('ok')
