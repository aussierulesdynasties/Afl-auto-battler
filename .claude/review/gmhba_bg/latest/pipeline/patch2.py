import os
H = os.path.dirname(os.path.abspath(__file__))
for f, a, b in [('tex_bake.py', "mean = (0.86 + 0.26 * 0.5) / 1.12   # the old average multiplier 0.99, stored /1.12 (linear)\nsave('court_grain.png', np.repeat(enc(mean * (1 + 0.052 * acc))", "mean = (0.86 + 0.26 * 0.5) / 1.25   # the old average multiplier 0.99, stored /1.25 (linear, headroom for the grain)\nsave('court_grain.png', np.repeat(enc(mean * (1 + 0.11 * acc))"),
                ('tex_bake.py', "MapRange 0.86..1.12; stored /1.12.", "MapRange 0.86..1.12; stored /1.25 (grain widened to meet grey std >= 10)."),
                ('scene.py', "(*[1.12 * c for c in srgb(rgb)], 1); nt.links.new(gt.outputs['Color'], mx.inputs[7])   # grain stored / 1.12", "(*[1.25 * c for c in srgb(rgb)], 1); nt.links.new(gt.outputs['Color'], mx.inputs[7])   # grain stored / 1.25")]:
    p = os.path.join(H, f); s = open(p, encoding='utf-8', newline='').read(); assert s.count(a) == 1, a[:40]
    open(p, 'w', encoding='utf-8', newline='').write(s.replace(a, b))
