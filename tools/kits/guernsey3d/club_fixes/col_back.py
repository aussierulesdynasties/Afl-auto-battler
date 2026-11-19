# col_back.py: Collingwood's back, rebuilt in the straight front photo's frame (both are AFL Store renders from one rig:
# same size, same hem). The only back photo is three-quarter, so it gives the measurements, not the pixels:
#  - outline = the front's outline row by row (the back collar shows through the front's V; the V is filled)
#  - stripes start 285 px above the hem at the centre (back photo: stripes from row 900, hem 1185) and copy the
#    front's stripe columns (white stripe on the centre line front and back)
#  - above that the back is a black yoke; the outermost white stripe runs up each side to the armhole (35 px)
import numpy as np
from PIL import Image
f = np.asarray(Image.open('dl_col/afl_3.png').convert('RGB')).astype(int)
g = f.sum(2); cloth = g < 735
H, W = g.shape
BLACK = np.array([0x14, 0x14, 0x14]); WHITE = np.array([0xEE, 0xEE, 0xEE])
hem_c = np.nonzero(cloth[:, 625])[0].max(); ys = hem_c - 285
out = np.full((H, W, 3), 255, np.uint8)
src = g.copy(); src[995:1100, 815:970] = g[990, 815:970]          # the front's jock tag is not on the back
rows = np.nonzero(cloth.any(1))[0]
for y in rows:
    z = np.nonzero(cloth[y])[0]; L, R = z.min(), z.max()
    out[y, L:R + 1] = BLACK
    if y >= ys:
        wh = src[y, L:R + 1] > 300
        out[y, L:R + 1][wh] = WHITE
    elif y >= 505:
        out[y, L:L + 35] = WHITE; out[y, R - 34:R + 1] = WHITE
Image.fromarray(out).save('ref_raw/COL_back.png'); print('stripes from row', ys, 'hem', hem_c)
