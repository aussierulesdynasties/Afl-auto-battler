# Melbourne front: the red V's edge runs straight under the two AFL logos (measured off the photo
# either side of them: y = 771 + 0.97 (x - 925), mirrored on the right). Redraw it there as that line.
import numpy as np
from PIL import Image
p = 'design_MEL_front.png'
a = np.array(Image.open(p)).astype(float)
RED, NAVY = np.array([0xEB, 0x10, 0x23]), np.array([0x19, 0x31, 0x6E])
y0, y1 = 505, 750
ys = np.arange(y0, y1)[:, None].astype(float)
for xa, xb, mirror in ((655, 935, False), (1065, 1345, True)):
    xs = np.arange(xa, xb)[None, :].astype(float)
    xl = 2000 - 1 - xs if mirror else xs
    line = 771 + 0.97 * (xl - 925)
    t = np.clip(line - ys + 0.5, 0, 1)[..., None]  # 1 = above the line (red)
    blk = a[y0:y1, xa:xb]
    on = blk[..., 3:] > 0
    blk[..., :3] = np.where(on, t * RED + (1 - t) * NAVY, blk[..., :3])
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(p)
print('MEL V edge redrawn under the AFL logos')
