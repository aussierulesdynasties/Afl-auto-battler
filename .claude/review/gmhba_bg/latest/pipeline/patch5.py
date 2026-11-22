import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scene.py')
s = open(p, encoding='utf-8', newline='').read()
a0 = "gm = mat_img('ground', os.path.join(D, 'ground.png'), 0.8)\n"
a1 = "_nt.links.new(_mx.outputs[2], _lift.inputs[6]); _nt.links.new(_lift.outputs[2], _b.inputs['Base Color'])\n"
i, j = s.index(a0), s.index(a1) + len(a1)
s = s[:i] + ("# one texture only (glTF carries one base colour image): ground.png x ground_detail.png (4 m tile, x1.21 lift),\n"
             "# baked by bake_ground.py into prep/ground_baked.png\n"
             "_gb = os.path.join(D, 'ground_baked.png'); assert os.path.exists(_gb), 'run bake_ground.py ' + name + ' first'\n"
             "gm = mat_img('ground', _gb, 0.8)\n") + s[j:]
s = s.replace("_ud = ob.data.uv_layers.new(name='UVDetail'); _ud.data.foreach_set('uv', (uv * (2 * NE / 4.0)).astype(np.float32).ravel())\n", "")
open(p, 'w', encoding='utf-8', newline='').write(s)
