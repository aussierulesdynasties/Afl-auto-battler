s = open('pools.py', encoding='utf-8', newline='').read()
i = s.index('def _trim('); j = s.index('_W, _D, _C, _L = (')
s = s[:i] + '''def _trim(A, R):   # squared rect: width between the long sides, length between the end edges; OSM notches ignored
    u = R[1] - R[0]; u = u / np.linalg.norm(u); v = np.array([-u[1], u[0]])
    Pu, Pv = [], []
    for i in range(len(A)):
        a_, b_ = A[i], A[(i + 1) % len(A)]; e = b_ - a_; n_ = np.linalg.norm(e)
        if n_ < 8: continue
        (Pv if abs(e @ u) / n_ > 0.9 else Pu if abs(e @ v) / n_ > 0.9 else []).extend([a_, b_])
    if len(Pu) < 4 or len(Pv) < 4: return R
    pu, pv = np.array(Pu) @ u, np.array(Pv) @ v
    return np.array([u * a_ + v * b_ for a_, b_ in ((pu.min(), pv.min()), (pu.max(), pv.min()), (pu.max(), pv.max()), (pu.min(), pv.max()))])
''' + s[j:]
open('pools.py', 'w', encoding='utf-8', newline='').write(s); print('ok')
