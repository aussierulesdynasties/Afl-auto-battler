# polygons for chosen aerial-only water blobs (reference trace). Splits each blob into parts after an opening,
# keeps parts >250 m2, star polygon from centroid (36 rays). Writes json list [[ 'water', poly ], ...] and an overlay.
import numpy as np, json, math, sys
from scipy import ndimage
from PIL import Image, ImageDraw
lab = np.load('out/peoplefirst/ov/miss_lab.npy'); ids = [int(a) for a in sys.argv[1].split(',')]
s = np.asarray(Image.open('out/peoplefirst/ov/sat1400.png').convert('RGB').resize((1400, 1400), Image.BOX))
L = s.astype(float).mean(2)
im = Image.fromarray(s); d = ImageDraw.Draw(im); polys = []
for i in ids:
    m = (lab == i) & (L < 45)
    if i == 557: m[1194:1200, :] = False   # the two clubhouse ponds touch at a neck; cut there
    m = ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=4)); m = ndimage.binary_opening(m, iterations=7)
    pl, n = ndimage.label(m)
    for j in range(1, n + 1):
        pm = pl == j
        if pm.sum() < 250: continue
        cy, cx = ndimage.center_of_mass(pm); pts = []
        for k in range(36):
            a = 2 * math.pi * k / 36; r = 0
            while True:
                y, x = int(cy + (r + 1) * math.sin(a)), int(cx + (r + 1) * math.cos(a))
                if not (0 <= y < 1400 and 0 <= x < 1400 and pm[y, x]): break
                r += 1
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, outline=(255, 0, 255))
        polys.append(['water', [[round(x - 700, 1), round(700 - y, 1)] for x, y in pts]]); print(i, j, int(pm.sum()))
json.dump(polys, open('out/peoplefirst/ov/ponds.json', 'w'))
im.crop((200, 1050, 760, 1400)).resize((1120, 700)).save('out/peoplefirst/ov/ponds_poly.png')
