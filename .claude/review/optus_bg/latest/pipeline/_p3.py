c = open('clsfy.py', encoding='utf-8').read()
old = """    _bv = np.full((N, N), -1.0, np.float32); _bc = cls.copy()
    for k in range(len(names)):
        _f = _ndi.uniform_filter((cls == k).astype(np.float32), 15); _m = _f > _bv; _bv[_m] = _f[_m]; _bc[_m] = k
    cls = _bc"""
assert c.count(old) == 1
c = c.replace(old, """    def _major(cl, w):
        bv = np.full((N, N), -1.0, np.float32); bc = cl.copy()
        for k in range(len(names)):
            f = _ndi.uniform_filter((cl == k).astype(np.float32), w); m = f > bv; bv[m] = f[m]; bc[m] = k
        return bc
    _c15 = _major(cls, 15); _c5 = _major(cls, 5)
    # paving keeps its finer pattern (the forecourt's flowing pink, salmon and grey bands are 4-15 m wide)
    _pav = np.isin(_c15, [names.index('brick_light'), names.index('brick_dark'), names.index('concrete')])
    cls = np.where(_pav & np.isin(_c5, [names.index('brick_light'), names.index('brick_dark'), names.index('concrete')]), _c5, _c15)""")
open('clsfy.py', 'w', encoding='utf-8', newline='').write(c)
import json
p = 'spec/optus.json'; s = json.load(open(p))
s['aerial_classes'].update({'brick_light': [204, 150, 138], 'brick_dark': [214, 178, 152], 'concrete': [188, 182, 172]})
json.dump(s, open(p, 'w'), indent=1); print('ok')
