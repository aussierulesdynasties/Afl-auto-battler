p='bake_ground.py'; s=open(p,newline='').read()
a="shallow = np.array([96, 120, 118]"
ins=("from scipy import ndimage as _nd\n"
"_lab, _n = _nd.label(wm); _sz = _nd.sum(wm, _lab, range(1, _n + 1)) * m_ * m_\n"
"small = np.isin(_lab, 1 + np.nonzero(_sz < 20000)[0])          # golf ponds/creeks: dark all through, as the aerial shows\n")
assert a in s and 'small = ' not in s; s=s.replace(a,ins+a,1)
b="t = np.clip((deep[rr] - 0.5) / 0.45, 0, 1)[..., None]"
assert b in s; s=s.replace(b,"t = np.maximum(np.clip((deep[rr] - 0.5) / 0.45, 0, 1), 0.9 * small[rr])[..., None]",1)
open(p,'w',newline='').write(s); print('ok')
