import sys
p = sys.argv[1]; s = open(p, newline='').read()
old = "WV = _nb(_nb(WV, 'all'), 'any')   # opening drops single flat cells\n"
assert old in s
new = old + """_E = WV.copy()
while _nb(_E, 'all').any(): _E = _nb(_E, 'all')
_K = _E & WV
while True:   # keep only the sea body that holds the deepest interior cell
    _K2 = _nb(_K, 'any') & WV
    if (_K2 == _K).all(): break
    _K = _K2
WV = _K
_lz = ~WV.ravel(); VF[_lz, 2] = np.maximum(VF[_lz, 2], ZSEA + 1.7)   # land never dips under the sea plane
"""
s = s.replace(old, new)
s = s.replace("VF[_l, 0] / 250.0, VF[_l, 1] / 250.0", "VF[_l, 0] / 500.0, VF[_l, 1] / 500.0")
s = s.replace("rm.inputs['To Max'].default_value = 0.13", "rm.inputs['To Max'].default_value = glass_rough")
s = s.replace("def mat_facade(nm, path, rough_wall=0.8):", "def mat_facade(nm, path, rough_wall=0.8, glass_rough=0.13):")
s = s.replace("def build_class(cls, tex, tw, th, var=None):", "def build_class(cls, tex, tw, th, var=None, gr=0.13):")
s = s.replace("mat_facade('facade_' + cls + sfx, os.path.join(HERE, 'tex', tex)))", "mat_facade('facade_' + cls + sfx, os.path.join(HERE, 'tex', tex), 0.8, gr))")
o = "for _v in range(12): build_class('tower', 'fac/b%d.png' % _v, 3.6, 3.2, (_v, 12)); build_class('tower_far', 'fac/b%d.png' % _v, 3.6, 3.2, (_v, 12))"
assert o in s
s = s.replace(o, "for _v in range(6): build_class('tower', 'fac/t%d.png' % _v, 3.6, 3.2, (_v, 6), 0.32); build_class('tower_far', 'fac/t%d.png' % _v, 3.6, 3.2, (_v, 6), 0.32)")
open(p, 'w', newline='').write(s); print('ok')
