# Fit the fence ellipse to hand-picked fence points (x y pairs, metres): python3 kit/fit.py x1 y1 x2 y2 ...
import sys, math, numpy as np
P = np.array(list(map(float, sys.argv[1:]))).reshape(-1, 2); x, y = P[:, 0], P[:, 1]
M = np.stack([x * x, x * y, y * y, x, y], 1); A, B, C, D, E = np.linalg.lstsq(M, np.ones(len(x)), rcond=None)[0]
den = 4 * A * C - B * B; x0 = (B * E - 2 * C * D) / den; y0 = (B * D - 2 * A * E) / den; th = 0.5 * math.atan2(B, A - C); ct, st = math.cos(th), math.sin(th)
K = 1 + A * x0 * x0 + B * x0 * y0 + C * y0 * y0; Ap = A * ct * ct + B * ct * st + C * st * st; Cp = A * st * st - B * ct * st + C * ct * ct
a1, a2 = math.sqrt(K / Ap), math.sqrt(K / Cp)
u = (x - x0) * ct + (y - y0) * st; v = -(x - x0) * st + (y - y0) * ct; res = (np.sqrt((u / a1) ** 2 + (v / a2) ** 2) - 1) * 0.5 * (a1 + a2)
print('%.2f %.2f %.2f %.2f %.2f' % (x0, y0, a1, a2, math.degrees(th)), ' residuals', np.round(res, 2))
