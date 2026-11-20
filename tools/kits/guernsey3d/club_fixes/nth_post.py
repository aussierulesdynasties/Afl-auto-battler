# nth_post.py: NTH, after trace. The outer stripes are blue to the side seams (front: from the armhole down; back: the
# stripes below the white upper back), but the render's lit edge snaps to white in a few spots. White pixels within
# 110 px (front) / 40 px (back) of a row's side edge become blue. The front's SHINBONER (club word, white on the left stripe) is kept.
import numpy as np
from PIL import Image
B = (0x1D, 0x3C, 0x88); W = np.array((0xE2, 0xE2, 0xE2))
for side, (r0, r1) in (('front', (560, 1900)), ('back', (1310, 1900))):
    d = np.array(Image.open(f'design_NTH_{side}.png').convert('RGBA'))
    n = 0
    for r in range(r0, r1):
        xs = np.nonzero(d[r, :, 3] > 0)[0]
        if len(xs) < 100: continue
        w = 110 if side == 'front' else 40
        for x in list(range(xs[0], xs[0] + w)) + list(range(xs[-1] - w + 1, xs[-1] + 1)):
            if side == 'front' and 560 <= x <= 650 and 1620 <= r <= 1830: continue  # SHINBONER
            if d[r, x, 3] > 0 and np.abs(d[r, x, :3].astype(int) - W).sum() < 120:
                d[r, x, :3] = B; n += 1
    Image.fromarray(d).save(f'design_NTH_{side}.png'); print('nth_post', side, 'edge px to blue', n)
# Back shoulder tops: white cloth on the render's light grey left the top line notched (2-12 px). The line is redrawn
# from the photo's own top row per column (upper envelope of both shoulders, which are mirror images about x 1000).
D = [185, 200, 215, 230, 245, 260, 275, 290, 305, 320, 335, 350, 365, 380, 395, 400]
Y = [255, 265, 281, 283, 287, 296, 300, 302, 303, 303, 303, 306, 310, 314, 318, 319]
d = np.array(Image.open('design_NTH_back.png').convert('RGBA'))
n = 0
for x in list(range(600, 816)) + list(range(1185, 1401)):
    top = int(round(np.interp(abs(1000 - x), D, Y)))
    n += int((d[:top, x, 3] > 0).sum()); d[:top, x, 3] = 0
    for y in range(345, top - 1, -1):  # below the line down to row 345 every pixel is cloth: gaps take the one below
        if d[y, x, 3] < 255:
            d[y, x] = d[y + 1, x]; d[y, x, 3] = 255; n += 1
Image.fromarray(d).save('design_NTH_back.png'); print('nth_post back shoulder line px', n)
