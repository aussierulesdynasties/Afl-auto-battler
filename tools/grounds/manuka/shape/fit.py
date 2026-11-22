"""A smooth closed curve fitted to a traced edge: r(bearing) as a Fourier series about C, fitted robustly (points
more than 3 MAD off are dropped and the fit repeated). Also a plain ellipse fit for the published-size check."""
import math

import numpy as np


def fourier_fit(bs, r, order=8, iters=6):
    b = np.radians(np.asarray(bs, float)); r = np.asarray(r, float)
    ok = np.isfinite(r)
    def A(b):
        cols = [np.ones_like(b)]
        for k in range(1, order + 1):
            cols += [np.cos(k * b), np.sin(k * b)]
        return np.stack(cols, 1)
    for _ in range(iters):
        coef, *_ = np.linalg.lstsq(A(b[ok]), r[ok], rcond=None)
        res = r - A(b) @ coef
        mad = np.nanmedian(np.abs(res[ok])) * 1.4826 + 1e-6
        ok = np.isfinite(r) & (np.abs(res) < max(3 * mad, 0.4))
    f = lambda bb: A(np.radians(np.asarray(bb, float))) @ coef
    return f, coef, ok


def ellipse_fit(x, y):
    """Least-squares conic, returned as centre, half axes (a >= b) and the bearing of the long axis."""
    D = np.stack([x * x, x * y, y * y, x, y, np.ones_like(x)], 1)
    _, _, V = np.linalg.svd(D)
    A, B, Cc, Dd, E, F = V[-1]
    M = np.array([[A, B / 2], [B / 2, Cc]])
    c = np.linalg.solve(2 * M, [-Dd, -E])
    k = -(F + Dd * c[0] / 2 + E * c[1] / 2)
    w, U = np.linalg.eigh(M / k)
    ax = 1 / np.sqrt(w)
    i = int(np.argmax(ax))
    u = U[:, i]
    brg = math.degrees(math.atan2(u[0], u[1])) % 180
    return c, ax.max(), ax.min(), brg
