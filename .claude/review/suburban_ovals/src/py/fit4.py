import sys, math, json; sys.path.insert(0, 'py'); from cam import Cam
import numpy as np
from scipy.optimize import minimize
c = Cam(1291, horizon=600)
A_, B_, FD = 80.0, 65.0, 3.0
fence_px = [(100, 677), (400, 677), (1100, 697), (1300, 698), (1500, 703), (1750, 711)]
fc = [c.back(u, v) for u, v in fence_px]
def ell_d(t, d):
    x, y = A_ * math.cos(t), B_ * math.sin(t); nx, ny = x / A_**2, y / B_**2; nl = math.hypot(nx, ny)
    return np.array([x + d * nx / nl, y + d * ny / nl])
ts = np.linspace(0, 2 * math.pi, 4000); FEN = np.array([ell_d(t, FD) for t in ts])
def to_world(p, X, Z):
    cx, cy, psi = p      # psi = world heading of camera forward
    fw = np.array([math.cos(psi), math.sin(psi)]); rt = np.array([math.sin(psi), -math.cos(psi)])
    return np.array([cx, cy]) + Z * fw + X * rt
def cost(p):
    return sum(np.min(np.sum((FEN - to_world(p, X, Z))**2, axis=1)) for X, Z in fc)
best = None
for psi0 in np.radians(np.arange(60, 130, 5)):
    r = minimize(cost, [0, 40, psi0], method="Nelder-Mead", options={"xatol": 1e-3, "fatol": 1e-4, "maxiter": 4000})
    if best is None or r.fun < best.fun: best = r
p = best.x; print("pose", p[0], p[1], math.degrees(p[2]), "cost", best.fun)
for (u, v), (X, Z) in zip(fence_px, fc):
    w = to_world(p, X, Z); print((u, v), "world", w.round(2), "dist", round(float(np.sqrt(np.min(np.sum((FEN - w)**2, axis=1)))), 2))
json.dump({"pose": list(p)}, open("spec/t4_pose.json", "w"))
