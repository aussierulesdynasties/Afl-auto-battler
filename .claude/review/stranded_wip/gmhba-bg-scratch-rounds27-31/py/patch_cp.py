import sys
p=sys.argv[1]; t=open(p,newline='').read()
a="    _hs = height(_A[:, 0], _A[:, 1]); v, f, uv = _CP; o = len(v)\n"
assert t.count(a)==1
b="    _c = _A.mean(0)\n    if KFr is not None and np.hypot(*_c) < KFr[int((np.degrees(np.arctan2(_c[1], _c[0])) % 360) // 2)] + 2: continue   # under the ground model\n"+a
open(p,'w',newline='').write(t.replace(a,b)); print('ok')
