# gee_post.py: GEE front, rows the Ford-box fill coloured from the armhole binding are re-read from the photo
# (light photo pixel -> white, dark -> navy). Box rows only, cloth pixels only.
import numpy as np
from PIL import Image
W, N = (0xE3, 0xE5, 0xF1), (0x07, 0x33, 0x6D)
d = np.array(Image.open('design_GEE_front.png').convert('RGBA'))
p = np.array(Image.open('ref/GEE_front.png').convert('RGBA')).astype(int)
n = 0
for y0, y1, x0, x1 in [(670, 700, 1020, 1300), (720, 760, 1280, 1350)]:
    for y in range(y0, y1):
        for x in range(x0, x1):
            if d[y, x, 3] == 0 or p[y, x, 3] < 200: continue
            c = W if p[y, x, :3].sum() > 520 else N
            if tuple(d[y, x, :3]) != c: d[y, x, :3] = c; n += 1
Image.fromarray(d).save('design_GEE_front.png'); print('gee_post changed', n)
# Binding stitch dots (single white pixels inside the navy armhole binding) become navy.
N2 = np.array(N); nav = (np.abs(d[:, :, :3].astype(int) - N2).sum(2) < 60) & (d[:, :, 3] > 0); src = nav.copy(); m = 0
for y in range(700, 780):
    for x in range(1260, 1370):
        if d[y, x, 3] == 0 or src[y, x]: continue
        if src[y-3:y+4, x-3:x+4].mean() > 0.6: d[y, x, :3] = N; m += 1
Image.fromarray(d).save('design_GEE_front.png'); print('stitch dots', m)
