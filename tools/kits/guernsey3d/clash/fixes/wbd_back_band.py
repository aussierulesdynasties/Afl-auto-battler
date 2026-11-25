"""Western Bulldogs clash, back: the red band's top edge runs under the CoinSpot logo (its rocket badge
overlaps the band), so the trace can't see it there. Read off the photo either side of the logo it is one
straight line, (650, 1262) to (1400, 1296) in the cut's square; above it is white. Left of x 650 the
red side panel rises to the armpit and stays as traced.   python wbd_back_band.py   (work folder)"""
import numpy as np
from PIL import Image

fn = 'design_WBD_back.png'
a = np.array(Image.open(fn).convert('RGBA'))
WHITE = np.array([0xEE, 0xEC, 0xF7])
RED = np.array([0xD8, 0x10, 0x2A])
x0, x1, ytop = 650, 1300, 1040
for x in range(x0, x1):
    edge = 1262 + (x - 650) * 34 / 750
    col = a[ytop:int(edge) + 1, x, :3]
    red = np.abs(col.astype(int) - RED).sum(-1) < 90
    col[red] = WHITE
    # anti-aliased edge row: blend by coverage
    f = edge - int(edge)
    a[int(edge), x, :3] = (WHITE * (1 - f) + RED * f).astype(np.uint8)
Image.fromarray(a).save(fn)
print('wbd back band edge straightened')
