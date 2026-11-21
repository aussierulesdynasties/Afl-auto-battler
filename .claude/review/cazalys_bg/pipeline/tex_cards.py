"""Hand-drawn alpha cards for trees (no photo pixels). leaf_card.png: a cluster of leaves with sky gaps, colour ~1 so the
vertex colour sets the species tone. frond.png: one palm frond, midrib up the middle (v), leaflets angled to the tip."""
import os, math, numpy as np
from PIL import Image, ImageDraw
H = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(11)
S = 512; SS = 2
im = Image.new('RGBA', (S * SS, S * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
for i in range(5):     # twig lines
    a = rng.uniform(0, 2 * math.pi); d.line([(S * SS / 2, S * SS / 2), ((0.5 + 0.35 * math.cos(a)) * S * SS, (0.5 + 0.35 * math.sin(a)) * S * SS)], fill=(90, 80, 70, 255), width=3 * SS)
for i in range(420):   # leaves inside a lumpy disc, denser in the middle, gaps toward the edge
    a = rng.uniform(0, 2 * math.pi); rr = (rng.random() ** 0.7) * 0.46
    if rr > 0.3 and rng.random() < 0.45: continue
    cx, cy = (0.5 + rr * math.cos(a)) * S * SS, (0.5 + rr * math.sin(a)) * S * SS
    L = rng.uniform(14, 26) * SS; W = L * rng.uniform(0.38, 0.5); th = rng.uniform(0, math.pi)
    pts = [(cx + L * math.cos(t) * math.cos(th) - W * math.sin(t) * math.sin(th), cy + L * math.cos(t) * math.sin(th) + W * math.sin(t) * math.cos(th)) for t in np.linspace(0, 2 * math.pi, 14)]
    g = int(rng.uniform(150, 255)); d.polygon(pts, fill=(int(g * 0.93), g, int(g * 0.85), 255))
im.resize((S, S), Image.LANCZOS).save(os.path.join(H, 'tex', 'leaf_card.png'))
W_, L_ = 256, 1024
im = Image.new('RGBA', (W_ * SS, L_ * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
mx = W_ * SS / 2
for k in range(46):    # leaflets from base (v=1, bottom) to tip (top)
    t = k / 46; y = (0.96 - 0.92 * t) * L_ * SS; ln = (0.42 * math.sin(math.pi * (0.15 + 0.85 * t)) + 0.06) * W_ * SS
    for sd in (-1, 1):
        g = int(rng.uniform(170, 250)); tip = (mx + sd * ln, y - ln * 0.9)
        d.polygon([(mx, y), (mx + sd * ln * 0.5, y - ln * 0.35 + 5 * SS), tip, (mx + sd * ln * 0.5, y - ln * 0.5 - 5 * SS)], fill=(int(g * 0.9), g, int(g * 0.8), 255))
d.line([(mx, 0.98 * L_ * SS), (mx, 0.03 * L_ * SS)], fill=(180, 170, 120, 255), width=6 * SS)
im.resize((W_, L_), Image.LANCZOS).save(os.path.join(H, 'tex', 'frond.png'))
print('cards written')
