"""Replace the 1.5 m square strip with the exact triangulated land strip (shore_strip.npy), edge = traced quay line."""
P = 'scene.py'; s = open(P, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
a = s.index("    _L = np.load(os.path.join(D, 'shore_fine.npy'))"); b = s.index("    fob = mk_obj('bg_shore_land'")
s = s[:a] + ("    _T = np.load(os.path.join(D, 'shore_strip.npy'))\n"
             "    _fv = np.concatenate([_T.reshape(-1, 2), np.full((len(_T) * 3, 1), WZ + 2.0)], 1)\n"
             "    _ff = np.arange(len(_T) * 3).reshape(-1, 3)\n").replace('\n', nl) + s[b:]
open(P, 'w', newline='').write(s); print('ok')
