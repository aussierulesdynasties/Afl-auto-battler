import sys
p = sys.argv[1]; t = open(p, newline='').read()
a = """from scipy import ndimage as _ndi
WV = _ndi.binary_opening(WV, iterations=1); WV = _ndi.binary_fill_holes(WV) & (np.abs(ZF - ZSEA) < 2.0)
_lab, _nl = _ndi.label(WV); _sz = np.bincount(_lab.ravel()); _keep = np.zeros(_nl + 1, bool); _keep[1:] = _sz[1:] >= 12; WV = _keep[_lab]
_shore = WV & ~_ndi.binary_erosion(WV); _sand = ~WV & _ndi.binary_dilation(WV)
"""
b = """def _nb(M_, op):   # 4-neighbour erosion (all) / dilation (any), numpy only
    P_ = np.pad(M_, 1, constant_values=(op == 'all'))
    S_ = [P_[1:-1, 1:-1], P_[:-2, 1:-1], P_[2:, 1:-1], P_[1:-1, :-2], P_[1:-1, 2:]]
    return np.logical_and.reduce(S_) if op == 'all' else np.logical_or.reduce(S_)
WV = _nb(_nb(WV, 'all'), 'any')   # opening drops single flat cells
_shore = WV & ~_nb(WV, 'all'); _sand = ~WV & _nb(WV, 'any')
"""
assert t.count(a) == 1; open(p, 'w', newline='').write(t.replace(a, b)); print('ok')
