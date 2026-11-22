"""Hand-made facade tiles (one bay x one storey each). RGB = wall grain (near white, multiplied by the building's own
colour) where alpha 0; glass where alpha 255 (its own painted colour). Four low-rise and four tower patterns."""
import numpy as np
from PIL import Image, ImageDraw
rng = np.random.default_rng(7); S = 256
def grain(base=232, amp=10):
    n = rng.normal(0, 1, (S // 8, S // 8)); n = np.asarray(Image.fromarray(((n + 3) * 40).clip(0, 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32)
    f = rng.normal(0, 1, (S, S)) * 0.35
    v = base + (n / 255 - 0.47) * amp * 2 + f * amp * 0.4
    return np.repeat(v[..., None], 3, 2)
def glass(c, d, box, refl=True):
    x0, y0, x1, y1 = box; c = np.array(c, np.float32)
    for y in range(y0, y1):
        t = (y - y0) / max(y1 - y0, 1)
        col = c * (1.12 - 0.28 * t) if refl else c   # sky reflection brighter at the top of each pane
        d[y, x0:x1, :3] = col; d[y, x0:x1, 3] = 255
def frame(d, box, c, w=3):
    x0, y0, x1, y1 = box; d[y0:y0 + w, x0:x1, :3] = c; d[y1 - w:y1, x0:x1, :3] = c; d[y0:y1, x0:x0 + w, :3] = c; d[y0:y1, x1 - w:x1, :3] = c
    d[y0:y0 + w, x0:x1, 3] = 0; d[y1 - w:y1, x0:x1, 3] = 0; d[y0:y1, x0:x0 + w, 3] = 0; d[y0:y1, x1 - w:x1, 3] = 0
def new(base=232, amp=10):
    d = np.zeros((S, S, 4), np.float32); d[..., :3] = grain(base, amp); return d
def save(d, n): Image.fromarray(d.clip(0, 255).astype(np.uint8), 'RGBA').save('tex/%s.png' % n); print(n)
# low-rise
d = new(); glass((70, 86, 100), d, (40, 60, 216, 190)); frame(d, (40, 60, 216, 190), (210, 210, 206)); d[190:200, 30:226, :3] = 200; save(d, 'fac_low_a')   # one square window, sill
d = new(236, 8); glass((60, 78, 94), d, (0, 80, 256, 170)); [frame(d, (x, 80, x + 64, 170), (90, 92, 94), 2) for x in range(0, 256, 64)]; save(d, 'fac_low_b')   # ribbon window, mullions
d = new(226, 14); glass((54, 66, 76), d, (64, 20, 192, 236)); frame(d, (64, 20, 192, 236), (150, 150, 146), 4); d[118:130, 64:192, :3] = 140; d[118:130, 64:192, 3] = 0; save(d, 'fac_low_c')   # tall window, transom
d = new(218, 22)
for y in range(0, S, 16): d[y:y + 2, :, :3] *= 0.86   # brick coursing
for y in range(0, S, 32):
    for x in range(0, S, 48): d[y:y + 16, x:x + 2, :3] *= 0.88; d[y + 16:y + 32, x + 24:x + 26, :3] *= 0.88
glass((48, 60, 70), d, (70, 70, 186, 200)); frame(d, (70, 70, 186, 200), (236, 234, 228), 5); save(d, 'fac_low_d')   # brick, punched window
# towers
d = new(); glass((70, 118, 160), d, (0, 0, 256, 256)); [frame(d, (x, 0, x + 64, 256), (40, 60, 80), 3) for x in range(0, 256, 64)]; d[0:6, :, :3] = 40; d[0:6, :, 3] = 0; save(d, 'fac_tow_a')   # blue curtain wall, fins
d = new(); glass((36, 48, 64), d, (0, 40, 256, 256)); [frame(d, (x, 40, x + 128, 256), (30, 36, 44), 2) for x in (0, 128)]; save(d, 'fac_tow_b')   # dark glass, white floor band (wall colour)
d = new(240, 6); glass((90, 108, 120), d, (24, 30, 232, 226)); [frame(d, (x, 30, x + 52, 226), (230, 230, 226), 3) for x in range(24, 232, 52)]; save(d, 'fac_tow_c')   # white concrete grid
d = new(); glass((88, 112, 104), d, (0, 0, 256, 220)); [frame(d, (x, 0, x + 43, 220), (120, 130, 126), 2) for x in range(0, 256, 43)]; save(d, 'fac_tow_d')   # green-grey glass, spandrel
# shed: corrugated sheeting (vertical ribs), dark roller door with slats, concrete plinth; tile = 6 m x 4.5 m (one door)
d = new(230, 8)
for x in range(0, S, 8): d[:, x:x + 2, :3] *= 0.80; d[:, x + 2:x + 3, :3] *= 1.06
d[226:, :, :3] = 168   # plinth
d[70:226, 70:186, :3] = 96
for y in range(70, 226, 6): d[y:y + 1, 70:186, :3] = 72   # door slats
d[64:70, 64:192, :3] = 120; d[70:226, 64:70, :3] = 120; d[70:226, 186:192, :3] = 120   # door frame
save(d, 'fac_shed')
