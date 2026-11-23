p='scene.py'; s=open(p,newline='').read()
a="""        N_ = np.array(N_); C = Q + N_ * off; A = C + N_ * w / 2; B = C - N_ * w / 2
        za = height(A[:, 0], A[:, 1]) + lift; zb = height(B[:, 0], B[:, 1]) + lift; s0 = len(V)
        for i in range(n):
            V.append((A[i, 0], A[i, 1], float(za[i]))); V.append((B[i, 0], B[i, 1], float(zb[i])))
        for i in range(n - 1):
            F.append((s0 + 2 * i, s0 + 2 * i + 1, s0 + 2 * i + 3, s0 + 2 * i + 2))"""
b="""        N_ = np.array(N_); C = Q + N_ * off; m = max(1, int(math.ceil(w / 1.5))); s0 = len(V)   # a column every 1.5 m across, so the strip follows the ground's crown
        for k in range(m + 1):
            X = C + N_ * (w / 2 - w * k / m); z = height(X[:, 0], X[:, 1]) + lift
            V.extend((float(X[i, 0]), float(X[i, 1]), float(z[i])) for i in range(n))
        for k in range(m):
            for i in range(n - 1):
                F.append((s0 + k * n + i, s0 + (k + 1) * n + i, s0 + (k + 1) * n + i + 1, s0 + k * n + i + 1))"""
assert a in s; s=s.replace(a,b)
a="roads.append((_dens(P, 3.0), WDR[hw], two))"; assert a in s; s=s.replace(a,"roads.append((_dens(P, 1.5), WDR[hw], two))")
open(p,'w',newline='').write(s); print('ok')
