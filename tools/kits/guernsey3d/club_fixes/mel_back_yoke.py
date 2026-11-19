# Melbourne back: the red yoke meets the navy on one smooth seam. The photo's seam rows, measured
# column by column (x 700-1300), are fitted with a gentle curve and the seam is redrawn on it,
# between the armhole bindings (columns that are navy just below the seam).
import numpy as np
from PIL import Image
src = np.array(Image.open('ref/MEL_back_photo.png').convert('RGB')).astype(int)
xs, ys = [], []
for x in range(640, 1361, 10):
    col = src[420:600, x]; red = col[:, 0] > col[:, 2] + 60
    ch = [i + 420 for i in range(1, len(col)) if red[i - 1] and not red[i] and i + 420 > 470]
    if ch:
        xs.append(x); ys.append(ch[0])
co = np.polyfit(xs, ys, 2)
p = 'design_MEL_back.png'
a = np.array(Image.open(p)).astype(float)
RED, NAVY = np.array([0xEB, 0x10, 0x23]), np.array([0x19, 0x31, 0x6E])
for x in range(a.shape[1]):
    if a[540, x, 3] == 0 or abs(a[540, x, :3] - NAVY).sum() > 30:
        continue
    seam = np.polyval(co, x)
    yy = np.arange(455, 525).astype(float)
    t = np.clip(seam - yy + 0.5, 0, 1)[:, None]
    a[455:525, x, :3] = t * RED + (1 - t) * NAVY
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(p)
print('MEL back yoke seam redrawn, rows', [round(np.polyval(co, x)) for x in (700, 1000, 1300)])
