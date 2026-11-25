"""Brisbane clash, front: the maroon yoke's bottom edge runs under the youi box's lower edge, and the box
fill dragged the maroon down there (a step). On the photo the edge is one gentle line; fit it to the
photo's own edge either side of the box (ref/BRL_front.png, the cut's square) and redraw maroon above it,
gold below, between the armholes.   python brl_front_yoke.py   (work folder, after trace_clash.py)"""
import numpy as np
from PIL import Image

fn = 'design_BRL_front.png'
a = np.array(Image.open(fn).convert('RGBA'))
r = np.array(Image.open('ref/BRL_front.png').convert('RGB')).astype(int)
MAROON = np.array([0x71, 0x2A, 0x39])
GOLD = np.array([0xEC, 0xB9, 0x50])
pts = []
for x in list(range(720, 970, 10)) + list(range(1220, 1300, 10)):
    col = r[560:760, x]
    g = (col[:, 0] > 180) & (col[:, 1] > 130) & (col[:, 2] < 120)
    if g.any():
        pts.append((x, 560 + np.argmax(g)))
p = np.array(pts, float)
fit = np.polyfit(p[:, 0], p[:, 1], 2)
print('yoke edge', fit)
for x in range(720, 1300):
    e = np.polyval(fit, x)
    # under the box (x 988-1212) the drag reaches 35 rows below the edge; elsewhere only the edge's own rows,
    # so the lion's ears (from row 677 down) stay
    lo, hi = (int(e) - 40, 700) if 988 <= x < 1212 else (int(e) - 6, int(e) + 7)
    for y in range(lo, hi):
        px = a[y, x]
        if px[3] == 0:
            continue
        if min(np.abs(px[:3].astype(int) - MAROON).sum(), np.abs(px[:3].astype(int) - GOLD).sum()) > 120 \
                and px[:3].astype(int).sum() < 600:
            continue          # dark marks stay; light specks (box-edge glints) are cloth
        f = np.clip(y + 1 - e, 0, 1)   # coverage of gold in this row
        px[:3] = (MAROON * (1 - f) + GOLD * f).astype(np.uint8)
# the gold lettering printed inside the back of the neck shows through the opening: it is not on the front
top = a[:420]
gold = (np.abs(top[..., :3].astype(int) - GOLD).sum(-1) < 200) & (top[..., 3] > 0)
top[gold, :3] = MAROON
Image.fromarray(a).save(fn)
print('brl front yoke edge straightened')
