"""COX lodged plans (1:250, pages share one frame, 150 dpi renders in hplans/) -> model metres, via the two light-tower
base circles on the demolition plan (h05: SE (231.5,1058.5), NE (4729.5,1058.5))."""
import numpy as np
P = np.array([[231.5, 1058.5], [4729.5, 1058.5]]); W = np.array([[105.29, -75.82], [65.65, 112.08]])
p = np.conj(P[:, 0] + 1j * P[:, 1]); w = W[:, 0] + 1j * W[:, 1]
A = (w[1] - w[0]) / (p[1] - p[0]); B = w[0] - A * p[0]
def pl2m(u, v):
    z = A * np.conj(np.asarray(u) + 1j * np.asarray(v)) + B; return np.real(z), np.imag(z)
def m2pl(x, y):
    z = np.conj((np.asarray(x) + 1j * np.asarray(y) - B) / A); return np.real(z), np.imag(z)
