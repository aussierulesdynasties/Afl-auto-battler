import sys
p = sys.argv[1]; s = open(p, encoding='utf-8', newline='').read()
a = "REG = np.stack([_bl(SA[..., c] * farm, 12) / np.maximum(_fw, 1e-3) for c in range(3)], -1)"
assert a in s
b = """_k = (2 * 12 + 1) ** 2; _fw = _fw / _k; _gm = np.array([np.median(SA[..., c][farm]) for c in range(3)], np.float32)
REG = np.stack([_bl(SA[..., c] * farm, 12) / _k / np.maximum(_fw, 0.05) for c in range(3)], -1)
_tw = np.clip(_fw / 0.3, 0, 1)[..., None]; REG = REG * _tw + _gm * (1 - _tw)"""
s = s.replace(a, b); open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
