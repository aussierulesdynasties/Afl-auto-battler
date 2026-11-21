import shutil
H = 'D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad/proto/'
def sub(fn, a, b):
    s = open(H + fn, newline='').read()
    if '\r\n' in s: a, b = a.replace('\n', '\r\n'), b.replace('\n', '\r\n')
    assert s.count(a) == 1, (fn, a[:60], s.count(a))
    open(H + fn, 'w', newline='').write(s.replace(a, b))
shutil.copy(H + 'scene.py', H + 'scene.py.bak_tower')
sub('scene.py', "def build_class(cls, tex, tw, th):", "def build_class(cls, tex, tw, th, var=None, nvar=1):")
sub('scene.py', "        if b['c'] != cls: continue\n        P = np.array(b['p'], float)",
    "        if b['c'] != cls: continue\n"
    "        if var is not None and int(abs(b['p'][0][0] * 7.31 + b['p'][0][1] * 13.17)) % nvar != var: continue   # facade variant: stable per building\n"
    "        P = np.array(b['p'], float)")
sub('scene.py', "    ob = mk_obj('bg_bld_' + cls, verts, faces, mat_facade('facade_' + cls, os.path.join(HERE, 'tex', tex)))",
    "    _sx = '' if var is None else '_v%d' % var\n"
    "    ob = mk_obj('bg_bld_' + cls + _sx, verts, faces, mat_facade('facade_' + cls + _sx, os.path.join(HERE, 'tex', tex)))")
sub('scene.py', "build_class('block', 'wall.png', 3.6, 3.2)\nbuild_class('tower', 'tower.png', 3.0, 3.6)",
    "# several hand-made facades per class (tex_towers.py + texture session's city_office/city_far), one per building\n"
    "for _i, (_t, _w, _h) in enumerate([('wall.png', 3.6, 3.2), ('adl_conc.png', 3.0, 3.6), ('adl_band.png', 6.0, 3.6)]): build_class('block', _t, _w, _h, _i, 3)\n"
    "for _i, (_t, _w, _h) in enumerate([('city_office.png', 3.0, 3.6), ('city_far.png', 12.0, 14.4), ('adl_conc.png', 3.0, 3.6), ('adl_fin.png', 6.0, 3.6), ('adl_band.png', 6.0, 3.6)]): build_class('tower', _t, _w, _h, _i, 5)")
print('ok')
