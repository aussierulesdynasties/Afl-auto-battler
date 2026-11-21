import os
H = os.path.dirname(os.path.abspath(__file__))
for f, a, b in [('scene.py', "set_uv_box(ob.data, 2.8 / 16)   # leaf_clumps.png tile = 8 cells of 2/2.8 m (cells doubled to match the old blotch size)", "set_uv_box(ob.data, 2.8 / 8)   # leaf_clumps.png tile = 8 cells of 1/2.8 m"),
                ('tex_bake.py', "k = 2.8 * 0.6", "k = 0.3   # matched by eye to the old Bump node (strength 0.6), which rendered soft")]:
    p = os.path.join(H, f); s = open(p, encoding='utf-8', newline='').read(); assert s.count(a) == 1, a[:40]
    open(p, 'w', encoding='utf-8', newline='').write(s.replace(a, b))
