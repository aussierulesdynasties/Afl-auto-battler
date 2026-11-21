# hand-made CBD tower facades (numpy), one floor tall (3.6 m) x 6 m wide per tile, 80 px/m.
# RGB = detail multiplier (building colour comes from the vertex colour = palette walls_tower: glass blue-greens, concrete, sandstone);
# alpha = small gloss mix (glass panes 0.3 with a pale sky tint, solid parts 0). Pixel (0,0) is always solid spandrel (roof plant box uses it).
# Also adl_oval_grass.png: 1024 px = 48 m, mown stripes 8 m + blade grain + a few worn patches (Oval No.2).
import numpy as np, os
from PIL import Image
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex'); R = np.random.default_rng(23)
def fnoise(h, w, s):
    f = np.fft.fft2(R.standard_normal((h, w)))
    ky, kx = np.meshgrid(np.fft.fftfreq(h), np.fft.fftfreq(w), indexing='ij')
    im = np.real(np.fft.ifft2(f * np.exp(-(kx ** 2 + ky ** 2) * (np.pi * s) ** 2 / 2))); return im / im.std()
PX = 80; W, H = 6 * PX, int(3.6 * PX)
y, x = np.mgrid[0:H, 0:W] / PX   # metres; y down from floor top
def build(name, solid, pane_cols, glass_v=0.42, solid_v=0.92, sky=(0.78, 0.86, 0.92)):
    """solid: bool mask (metres grid) of spandrel/mullion/wall; pane_cols: pane width (m) for per-pane brightness"""
    v = np.where(solid, solid_v, glass_v).astype(float)
    pane = (x // pane_cols).astype(int) % int(round(6 / pane_cols))
    pv = R.uniform(0.8, 1.2, int(round(6 / pane_cols)))[pane]   # tiles across: whole panes per tile
    v = np.where(solid, v * (1 + 0.03 * fnoise(H, W, 6)), v * pv)
    rgb = np.stack([v] * 3, -1)
    a = np.where(solid, 0.0, 0.3)
    rgb = np.where(solid[..., None], rgb, rgb * 0.7 + 0.3 * np.array(sky) * glass_v * 1.6)
    assert solid[0, 0]
    im = np.dstack([np.clip(rgb * 255, 0, 255), a * 255]).astype(np.uint8)
    Image.fromarray(im, 'RGBA').save(os.path.join(OUT, name)); print(name, round(float(v.mean()), 3))
# A curtain wall: 0.9 m spandrel band per floor, mullions every 1.5 m
build('cbd_curtain.png', (y < 0.9) | ((x % 1.5) < 0.08), 1.5)
# B concrete grid: punched 1.6 x 1.8 m windows at 3 m pitch
build('cbd_punched.png', ~(((x % 3.0) > 0.7) & ((x % 3.0) < 2.3) & (y > 1.0) & (y < 2.8)), 3.0, glass_v=0.32)
# C sandstone: tall narrow windows 1.0 x 2.0 at 2 m pitch, warm stone multiplier
build('cbd_stone.png', ~(((x % 2.0) > 0.5) & ((x % 2.0) < 1.5) & (y > 0.9) & (y < 2.9)), 2.0, glass_v=0.3, solid_v=0.97, sky=(0.7, 0.75, 0.8))
# D vertical fins 0.35 m every 1.5 m, thin slab edge
build('cbd_fins.png', ((x % 1.5) < 0.35) | (y < 0.3), 1.5, solid_v=0.98)
# E ribbon windows: 1.7 m solid band, 1.9 m glass band, mullions every 2 m
build('cbd_ribbon.png', (y < 1.7) | ((x % 2.0) < 0.06), 2.0, glass_v=0.38)
# Oval No.2 grass
n = 1024; m = 48 / n; yy, xx = np.mgrid[0:n, 0:n] * m
g = np.array([172, 152, 104], float) / 255
stripe = 1 + 0.06 * np.sign(np.sin(2 * np.pi * xx / 16))   # 8 m mown stripes (48 m = 3 periods)
grain = 1 + 0.07 * fnoise(n, n, 1.5) + 0.05 * fnoise(n, n, 8)
v = stripe * grain
rgb = g[None, None] * v[..., None]
worn = np.clip((fnoise(n, n, 70) - 1.6) * 0.6, 0, 1) * np.clip(0.6 + 0.4 * fnoise(n, n, 4), 0, 1)   # a few worn patches
dry = np.array([160, 142, 100], float) / 255
rgb = rgb * (1 - worn[..., None]) + dry[None, None] * grain[..., None] * worn[..., None]
print('worn frac', round(float((worn > 0.3).mean()), 3))
Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8)).save(os.path.join(OUT, 'adl_oval_grass.png'))
