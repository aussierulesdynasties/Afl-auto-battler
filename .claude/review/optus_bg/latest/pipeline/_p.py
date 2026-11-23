s = open('prep.py', encoding='utf-8').read()
a = "# road / water mask for the ground material's"
assert s.count(a) == 1
s = s.replace(a, "exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clsfy.py'), encoding='utf-8').read())\n" + a)
open('prep.py', 'w', encoding='utf-8', newline='').write(s)
c = open('clsfy.py', encoding='utf-8').read()
old = """    _oh = np.stack([_ndi.uniform_filter((cls == k).astype(np.float32), 5) for k in range(len(names))], 0)
    cls = _oh.argmax(0)"""
assert c.count(old) == 1
c = c.replace(old, """    _bv = np.full((N, N), -1.0, np.float32); _bc = cls.copy()
    for k in range(len(names)):
        _f = _ndi.uniform_filter((cls == k).astype(np.float32), 5); _m = _f > _bv; _bv[_m] = _f[_m]; _bc[_m] = k
    cls = _bc""")
open('clsfy.py', 'w', encoding='utf-8', newline='').write(c); print('ok')
