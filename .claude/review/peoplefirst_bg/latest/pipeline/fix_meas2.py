p='meas_table.py'; s=open(p,encoding='utf-8').read()
a="    d.append(np.abs(np.median(s[m], 0) - np.median(t0[m], 0)).mean()); n += 1   # roofs: raw render (lit roofs are not darkened by the terrain gain)"
b="    d.append((np.median(s[m], 0), np.median(t0[m], 0))); n += 1"
assert s.count(a)==1; s=s.replace(a,b)
a2="d = np.array(d)\n"
b2=("_A = np.array([q[0] for q in d]); _M = np.array([q[1] for q in d]); _ok = _M.max(1) < 250   # fit roof gain on unsaturated roofs\n"
    "RG = np.median(_A[_ok] / np.maximum(_M[_ok], 1), 0); d = np.abs(_A - np.clip(_M * RG, 0, 255)).mean(1)\n"
    "rows.append(('Roof render-to-satellite gain (fitted on roofs)', '', ', '.join('%.2f' % g for g in RG), ''))\n")
assert s.count(a2)==1; s=s.replace(a2,b2); open(p,'w',encoding='utf-8').write(s); print('ok')
