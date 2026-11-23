s = open('pools.py', encoding='utf-8', newline='').read()
a = "    if abs(_area(_A)) > 0.80 * _ra and len(_A) <= 8: _A = _R   # squared: OSM steps on a rectangular pool are tracing noise\n"
assert a in s
b = a.replace("_A = _R   #", "_A = _trim(_A, _R)   #")
s = s.replace(a, b)
f = "_W, _D, _C, _L = ("
s = s.replace(f, '''def _trim(A, R):   # squared rect from long edges only (>8 m): short OSM notches at pool ends do not widen it
    u = R[1] - R[0]; u = u / np.linalg.norm(u); v = np.array([-u[1], u[0]])
    P = [p for i in range(len(A)) for p in (A[i], A[(i + 1) % len(A)]) if np.linalg.norm(A[(i + 1) % len(A)] - A[i]) > 8]
    if len(P) < 4: return R
    P = np.array(P); pu, pv = P @ u, P @ v
    return np.array([u * a_ + v * b_ for a_, b_ in ((pu.min(), pv.min()), (pu.max(), pv.min()), (pu.max(), pv.max()), (pu.min(), pv.max()))])
''' + f, 1)
open('pools.py', 'w', encoding='utf-8', newline='').write(s); print('ok')
