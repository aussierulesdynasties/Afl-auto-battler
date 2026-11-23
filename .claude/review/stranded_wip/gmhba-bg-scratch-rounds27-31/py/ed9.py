import sys
p = sys.argv[1]; s = open(p, newline='').read()
i = s.index("_E = WV.copy()\n"); j = s.index("WV = _K\n") + len("WV = _K\n")
s = s[:i] + """_left = WV.copy(); _K = np.zeros_like(WV); _min = max(50, int(WV.sum() * 0.02))
while _left.any():   # keep every water body of at least 2% of the flat sea-level cells; drop small inland flats
    _r, _c = np.argwhere(_left)[0]; _C = np.zeros_like(WV); _C[_r, _c] = True
    while True:
        _C2 = _nb(_C, 'any') & WV
        if (_C2 == _C).all(): break
        _C = _C2
    if _C.sum() >= _min: _K |= _C
    _left &= ~_C
print('far water bodies kept', int(_K.sum()), 'of', int(WV.sum()))
WV = _K
""" + s[j:]
open(p, 'w', newline='').write(s); print('ok')
