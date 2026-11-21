# hand-made facade tiles for Adelaide towers/blocks (numpy). RGB = colour, alpha 1 = glass (texture colour shown),
# alpha 0 = wall (texture x building colour). Tiles are one bay x one floor, so windows line up with storeys.
import numpy as np, os, sys
from PIL import Image
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex')
R = np.random.default_rng(7)
def noise(h, w, s, amp):
    # periodic (tileable) noise: white noise low-passed in the frequency domain, feature size ~s px
    f = np.fft.fft2(R.standard_normal((h, w)))
    ky, kx = np.meshgrid(np.fft.fftfreq(h), np.fft.fftfreq(w), indexing='ij')
    im = np.real(np.fft.ifft2(f * np.exp(-(kx ** 2 + ky ** 2) * (np.pi * s) ** 2 / 2)))
    im = (im - im.min()) / (im.max() - im.min())
    return (im - 0.5) * amp
def glass(h, w, top, bot):
    t = np.linspace(0, 1, h)[:, None, None]
    return np.broadcast_to(np.array(top) * (1 - t) + np.array(bot) * t, (h, w, 3)).copy()
def save(rgb, a, nm):
    im = np.dstack([np.clip(rgb, 0, 255), np.clip(a * 255, 0, 255)]).astype(np.uint8)
    Image.fromarray(im, 'RGBA').save(os.path.join(OUT, nm)); print(nm, im.shape)
n = 256; y, x = np.mgrid[0:n, 0:n] / n
# adl_conc.png = 3.0 m bay x 3.6 m floor: precast concrete, one punched window 1.8 x 1.9 m, reveal shadow on top/left
rgb = np.full((n, n, 3), 205.0) + noise(n, n, 16, 18)[..., None] + noise(n, n, 3, 8)[..., None]; a = np.zeros((n, n))
win = (x > 0.2) & (x < 0.8) & (y > 0.3) & (y < 0.83)
rgb[win] = glass(n, n, (70, 86, 102), (38, 46, 58))[win] + noise(n, n, 32, 14)[win][..., None]; a[win] = 1
rev = ((x > 0.2) & (x < 0.23) & (y > 0.3) & (y < 0.83)) | ((y > 0.3) & (y < 0.33) & (x > 0.2) & (x < 0.8))
rgb[rev] = 120; a[rev] = 0
sill = (y > 0.83) & (y < 0.86) & (x > 0.18) & (x < 0.82); rgb[sill] = 230; a[sill] = 0
save(rgb, a, 'adl_conc.png')
# adl_fin.png = 6.0 m x 3.6 m floor: full-height glass behind pale vertical fins every 1.5 m, slab edge band
rgb = glass(n, n, (96, 116, 132), (52, 64, 78)) + noise(n, n, 64, 20)[..., None]; a = np.ones((n, n))
fin = np.abs(((x * 4) % 1) - 0.5) > 0.44; rgb[fin] = 215 + noise(n, n, 8, 10)[fin][..., None]; a[fin] = 0
slab = y > 0.88; rgb[slab] = 180 + noise(n, n, 8, 10)[slab][..., None]; a[slab] = 0
sh = (~fin) & (np.abs(((x * 4) % 1) - 0.5) > 0.38); rgb[sh] *= 0.8
save(rgb, a, 'adl_fin.png')
# adl_band.png = 6.0 m x 3.6 m floor: ribbon window 1.6 m tall over a solid 2.0 m spandrel, mullion every 1.5 m
rgb = np.full((n, n, 3), 190.0) + noise(n, n, 24, 16)[..., None] + noise(n, n, 3, 6)[..., None]; a = np.zeros((n, n))
rib = (y > 0.12) & (y < 0.56)
rgb[rib] = glass(n, n, (60, 74, 88), (34, 42, 52))[rib] + noise(n, n, 48, 18)[rib][..., None]; a[rib] = 1
mul = rib & (np.abs(((x * 4) % 1) - 0.5) > 0.485); rgb[mul] = 150; a[mul] = 0
ln = (y > 0.56) & (y < 0.58); rgb[ln] = 140; a[ln] = 0
save(rgb, a, 'adl_band.png')
