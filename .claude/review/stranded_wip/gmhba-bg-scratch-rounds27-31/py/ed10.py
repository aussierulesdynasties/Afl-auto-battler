import sys
p = sys.argv[1]; s = open(p, newline='').read()
o = "set_corner_col(_o.data, np.concatenate([vc[_l], np.ones((len(_l), 1))], 1)); set_uv(_o.data, np.stack([VF[_l, 0] / 500.0"
assert o in s
s = s.replace(o, "_svc = np.array(lin((122, 122, 110)))[None, :3] * (1 - hz) + np.array(lin(PAL['haze']))[None, :3] * hz; set_corner_col(_o.data, np.concatenate([_svc[_l], np.ones((len(_l), 1))], 1)); set_uv(_o.data, np.stack([VF[_l, 0] / 500.0")
open(p, 'w', newline='').write(s); print('ok')
