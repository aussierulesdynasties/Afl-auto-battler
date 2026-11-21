# GE view cameras for York Park captures. View 'lHHH' = 420 m, tilt 65, heading HHH; 'oHHH' = 700 m, tilt 50.
# Target altitude 5 m ASL; Z0 = the field's height in that frame (calibrated by overlaying the fence).
import sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import earthcam as E
Z0 = float(os.environ.get('Z0', 0.0))
def cam(v):
    h = int(v[1:]); d, t = (420, 65) if v[0] == 'l' else (700, 50)
    return E.cam(h, t, d, tz=0.0)
def P(v, X):  # X in model frame (z up from field) -> pixel
    X = np.asarray(X, float).copy(); X[..., 2] = X[..., 2] + Z0
    c = cam(v); return np.array([E.proj(c, x) for x in X.reshape(-1, 3)])
def z_at(v, x, y, py):  # height (above field) of the point at plan (x,y) seen at pixel row py
    lo, hi = -20.0, 80.0
    for _ in range(60):
        m = 0.5 * (lo + hi); q = P(v, [x, y, m])[0][1]
        if q > py: lo = m
        else: hi = m
    return 0.5 * (lo + hi)
