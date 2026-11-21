"""Gain so 50/50 of soft water (40 m tile) and a 0.37x-scale, 36.87 deg sample reaches sd >= 10 (measured on a 400 m patch)."""
from PIL import Image; import numpy as np
T = np.asarray(Image.open('tex/mv_harbour_water_soft.png').convert('L')).astype(float); N = T.shape[0]
def samp(x, y, tile):   # world metres -> texel, wrap, nearest
    return T[((y / tile) * N).astype(int) % N, ((x / tile) * N).astype(int) % N]
g = np.linspace(0, 400, 800); X, Y = np.meshgrid(g, g)
c, s = 0.8, 0.6
a = samp(X, Y, 40.0)
b = samp(c * X - s * Y, s * X + c * Y, 40.0 / 0.37)
m = 0.5 * a + 0.5 * b
k = max(1.0, 10.5 / m.std())
print('sd single', a.std().round(2), 'mix', m.std().round(2), 'gain', round(k, 3), 'mean', m.mean().round(1), 'sd after', (m.std() * k).round(2))
