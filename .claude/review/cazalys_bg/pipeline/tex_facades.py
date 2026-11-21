"""Hand-painted facade atlas (no photo pixels): 4x4 cells of 256 px, each cell = one bay 3.6 m wide x one storey 3.2 m.
RGB is a grey multiplier on the building's own colour where alpha = 0; alpha 1 = glass (drawn as is).
Cells 0-7 Cairns houses, 8-15 commercial / industrial. usage: tex_facades.py out_dir -> facades.png
"""
import os, sys
import numpy as np
from PIL import Image
out = sys.argv[1]; rng = np.random.default_rng(21)
N = 256; SX = N / 3.6; SY = N / 3.2

def base(g=0.95):
    C = np.zeros((N, N, 4)); C[..., :3] = g; return C
def px(x, y): return int(x * SX), N - int(y * SY)          # metres (from bay left, from floor) -> pixel
def rect(C, x0, y0, x1, y1, col, a=0):
    c0, r1 = px(x0, y0); c1, r0 = px(x1, y1); C[r0:r1, c0:c1, :3] = col; C[r0:r1, c0:c1, 3] = a
def glass(C, x0, y0, x1, y1, frame=0.9):
    rect(C, x0 - 0.06, y0 - 0.06, x1 + 0.06, y1 + 0.06, frame)
    c0, r1 = px(x0, y0); c1, r0 = px(x1, y1); t = np.linspace(0, 1, r1 - r0)[:, None, None]
    C[r0:r1, c0:c1, :3] = np.array([0.30, 0.37, 0.43]) * (1 - t) + np.array([0.12, 0.15, 0.19]) * t; C[r0:r1, c0:c1, 3] = 1
def hlines(C, y0, y1, step, dark=0.82, w=2):
    y = y0
    while y < y1:
        r = px(0, y)[1]; C[max(0, r - w):r, :, :3] *= dark; y += step
def vlines(C, step, dark=0.82, w=2, y0=0, y1=3.2):
    x = 0.0
    while x < 3.6:
        c = px(x, 0)[0]; C[px(0, y1)[1]:px(0, y0)[1], c:c + w, :3] *= dark; x += step
def louvres(C, x0, y0, x1, y1):
    glass(C, x0, y0, x1, y1)
    y = y0
    while y < y1:
        c0, r = px(x0, y); c1, _ = px(x1, y); C[r - 3:r, c0:c1, :3] = 0.78; C[r - 3:r, c0:c1, 3] = 0; y += 0.12
def screen(C, x0, y0, x1, y1):           # security screen: diamond grille over glass
    glass(C, x0, y0, x1, y1); c0, r1 = px(x0, y0); c1, r0 = px(x1, y1)
    yy, xx = np.mgrid[r0:r1, c0:c1]; m = ((xx + yy) % 14 < 2) | ((xx - yy) % 14 < 2)
    C[r0:r1, c0:c1][m, :3] = 0.25; C[r0:r1, c0:c1][m, 3] = 0
def bricks(C, y0=0, y1=3.2, mortar=0.88):
    bh, bw = 0.086, 0.23; r = 0
    y = y0
    while y < y1:
        rr = px(0, y)[1]; C[rr - 2:rr, :, :3] *= mortar
        off = (r % 2) * bw / 2; x = off
        while x < 3.6:
            c = px(x, 0)[0]; C[px(0, y + bh)[1]:rr, c:c + 2, :3] *= mortar; x += bw
        # per-brick tone
        y += bh; r += 1
    C[..., :3] *= 1 + 0.10 * (rng.random((N, N // 8, 1)).repeat(8, 1) - 0.5)
def awning(C, y, depth=0.35, g=0.35):
    rect(C, 0, y, 3.6, y + depth, g)

cells = []
# 0 weatherboard + louvres
C = base(); hlines(C, 0, 3.2, 0.18); louvres(C, 1.0, 1.0, 2.6, 2.3); rect(C, 0, 2.9, 3.6, 3.2, 0.7); cells.append(C)
# 1 fibro sheet with cover battens + window hood
C = base(); vlines(C, 1.2, 0.86, 3); hlines(C, 1.2, 1.3, 1, 0.86, 3); glass(C, 0.9, 0.9, 2.7, 2.2); rect(C, 0.7, 2.35, 2.9, 2.6, 0.55); cells.append(C)
# 2 besser block + sliding window
C = base(0.9)
for yy in np.arange(0.2, 3.2, 0.2): C[px(0, yy)[1] - 2:px(0, yy)[1], :, :3] *= 0.84
for i, yy in enumerate(np.arange(0, 3.2, 0.2)):
    for xx in np.arange((i % 2) * 0.2, 3.6, 0.4): c = px(xx, 0)[0]; C[px(0, yy + 0.2)[1]:px(0, yy)[1], c:c + 2, :3] *= 0.84
glass(C, 0.8, 1.0, 2.8, 2.2); rect(C, 1.77, 1.0, 1.83, 2.2, 0.9); cells.append(C)
# 3 rendered + aluminium window with security screen
C = base(); screen(C, 0.8, 0.9, 2.8, 2.2); cells.append(C)
# 4 Queenslander: lattice skirt below a verandah rail, weatherboard above
C = base(); hlines(C, 1.2, 3.2, 0.18)
c0, r1 = px(0, 0); c1, r0 = px(3.6, 1.1); yy, xx = np.mgrid[r0:r1, c0:c1]
m = ((xx + yy) % 18 < 4) | ((xx - yy) % 18 < 4); sub = C[r0:r1, c0:c1]; sub[~m, :3] = 0.18; C[r0:r1, c0:c1] = sub
rect(C, 0, 1.1, 3.6, 1.25, 0.98); louvres(C, 1.2, 1.6, 2.4, 2.8); cells.append(C)
# 5 face brick + window
C = base(0.92); bricks(C); glass(C, 0.9, 0.9, 2.7, 2.2, 0.95); rect(C, 0.85, 0.82, 2.75, 0.9, 0.98); cells.append(C)
# 6 vertical board cladding + tall window
C = base(); vlines(C, 0.15, 0.84); glass(C, 1.3, 0.6, 2.3, 2.6); cells.append(C)
# 7 rendered, louvre pair, painted plinth
C = base(); louvres(C, 0.5, 1.1, 1.6, 2.4); louvres(C, 2.0, 1.1, 3.1, 2.4); rect(C, 0, 0, 3.6, 0.45, 0.72); cells.append(C)
# 8 tilt-up concrete panel with joints, no windows
C = base(0.9); vlines(C, 1.8, 0.62, 4); rect(C, 0, 2.6, 3.6, 2.7, 0.7); rect(C, 0, 0, 3.6, 0.3, 0.78); rect(C, 0.4, 0, 1.3, 2.1, 0.42); rect(C, 0.45, 0.05, 1.25, 2.05, 0.6); louvres(C, 2.2, 1.9, 3.3, 2.4); C[..., :3] *= 1 + 0.08 * (rng.random((N, 1, 1)) - 0.5); cells.append(C)
# 9 ribbed metal cladding
C = base(); vlines(C, 0.2, 0.78, 4); C[:, ::2, :3] *= 0.97; cells.append(C)
# 10 shopfront: glazing under an awning, painted parapet above
C = base(); glass(C, 0.1, 0.0, 3.5, 2.4, 0.4); rect(C, 1.6, 0, 1.68, 2.4, 0.4); awning(C, 2.55); cells.append(C)
# 11 office ribbon window
C = base(); glass(C, 0.0, 1.0, 3.6, 2.5, 0.6); rect(C, 1.75, 1.0, 1.85, 2.5, 0.6); cells.append(C)
# 12 block wall with high windows (warehouse office)
C = base(0.9)
for yy in np.arange(0.2, 3.2, 0.2): C[px(0, yy)[1] - 2:px(0, yy)[1], :, :3] *= 0.85
glass(C, 0.6, 2.2, 3.0, 2.8); cells.append(C)
# 13 rendered with louvre band and sunshade blades
C = base(); louvres(C, 0.2, 1.2, 3.4, 2.4)
for xx in np.arange(0.2, 3.6, 0.6): rect(C, xx, 1.1, xx + 0.08, 2.6, 0.55)
cells.append(C)
# 14 corrugated shed with roller door half
C = base(); vlines(C, 0.076, 0.86, 2); c0, r1 = px(0.3, 0); c1, r0 = px(3.3, 2.8)
sub = C[r0:r1, c0:c1]; sub[..., :3] = 0.85; sub[(np.arange(r1 - r0) % 6 < 2), :, :3] = 0.7; C[r0:r1, c0:c1] = sub; cells.append(C)
# 15 brick commercial with windows and a band
C = base(0.92); bricks(C); glass(C, 0.5, 1.0, 1.6, 2.4, 0.95); glass(C, 2.0, 1.0, 3.1, 2.4, 0.95); rect(C, 0, 2.7, 3.6, 2.85, 0.98); cells.append(C)

A = np.zeros((4 * N, 4 * N, 4))
for i, C in enumerate(cells):
    C[..., :3] *= 1 + 0.06 * (rng.random((N, N, 1)) - 0.5)                 # paint grain
    A[(i // 4) * N:(i // 4 + 1) * N, (i % 4) * N:(i % 4 + 1) * N] = C
Image.fromarray((np.clip(A, 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(out, 'facades.png'))
print('facades ok', len(cells))
