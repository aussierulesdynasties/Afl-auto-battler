import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex_bake.py')
s = open(P, encoding='utf-8', newline='').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:50]; s = s.replace(a, b)
rep("rng = np.random.default_rng(2808)\n", "rng = np.random.default_rng(2808)\ndef enc(v):   # linear multiplier 0..1 -> sRGB 0..255 (Blender and glTF decode colour textures as sRGB)\n    v = np.clip(v, 0, 1); return 255 * np.where(v <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055)\n")
rep("np.repeat((mr / 1.15 * 255)[..., None], 3, 2)", "np.repeat(enc(mr / 1.15)[..., None], 3, 2)")
rep("mean = (0.86 + 0.26 * 0.5) / 1.12 * 255   # the old average multiplier 0.99, stored /1.12\nsave('court_grain.png', np.repeat((mean + 10.5 * acc)[..., None], 3, 2))",
    "mean = (0.86 + 0.26 * 0.5) / 1.12   # the old average multiplier 0.99, stored /1.12 (linear)\nsave('court_grain.png', np.repeat(enc(mean * (1 + 0.052 * acc))[..., None], 3, 2))")
open(P, 'w', encoding='utf-8', newline='').write(s)
