"""St Kilda clash (2025 Hot Cross), front: above the cross's arm the photo shows the inside of the back
through deep armholes and the neck (white and pink lining), and the AFL and CIIC boxes cover the red, so
the trace came out in scraps. Read off the photo in the cut's square (ref/STK_front.png) the top is plain:
red, with the cross's black upright (x 777-995, straight down from the neck) and the black arm across the
chest (rows 749-899) with the club crest on it (x 1030-1215, rows 730-900, kept as traced).
    python stk_front_top.py   (work folder, after trace_clash.py)"""
import numpy as np
from PIL import Image

fn = 'design_STK_front.png'
a = np.array(Image.open(fn).convert('RGBA'))
RED = np.array([0xE4, 0x12, 0x34])
BLACK = np.array([0x37, 0x31, 0x3A])
X0, X1 = 777, 995          # the upright
ARM0, ARM1 = 749, 899      # the arm
CREST = (1030, 730, 1215, 900)
H, W = a.shape[:2]
yy, xx = np.mgrid[0:ARM1, 0:W]
cloth = a[:ARM1, :, 3] > 0
crest = (xx >= CREST[0]) & (xx < CREST[2]) & (yy >= CREST[1]) & (yy < CREST[3])
top = a[:ARM1]
paint = cloth & ~crest
upright = (xx >= X0) & (xx < X1)
top[paint & (yy < ARM0), :3] = RED
top[paint & (yy < ARM0) & upright, :3] = BLACK
top[paint & (yy >= ARM0), :3] = BLACK
Image.fromarray(a).save(fn)
print('stk front top redrawn')
