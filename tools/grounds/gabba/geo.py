import json, math, numpy as np
D = json.load(open('model_in5.json')); J = json.load(open('camB.json'))
C = np.array(J['C']); M = np.array(J['M']); f = J['f']; ccx = J['cx']; ccy = J['cy']
def pr(X):
    d = (np.array(X, float) - C) @ M.T; a, b = d[0] / d[2], d[1] / d[2]; g = 1 + 0.5 * (a * a + b * b); return (ccx + f * a * g, ccy - f * b * g)
def interp(a, xs, ys):
    a = (a + math.pi) % (2 * math.pi) - math.pi
    if a < xs[0] or a >= xs[-1]:
        x0, x1 = xs[-1], xs[0] + 2 * math.pi; aa = a if a >= xs[-1] else a + 2 * math.pi
        return ys[-1] + (ys[0] - ys[-1]) * (aa - x0) / (x1 - x0)
    lo, hi = 0, len(xs) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if xs[m] <= a: lo = m
        else: hi = m
    x0, x1 = xs[lo], xs[hi]
    return ys[lo] + (ys[hi] - ys[lo]) * (a - x0) / (x1 - x0) if x1 > x0 else ys[lo]
rF = lambda a: interp(a, *D['RF']); cx, cy = D['Cc']
def P(a, r, z): return (cx + r * math.cos(a), cy + r * math.sin(a), z)
B = D['booms']
