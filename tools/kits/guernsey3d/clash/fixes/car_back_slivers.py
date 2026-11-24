"""Carlton clash, back: inside the navy band down each armhole the photo shows slivers of the white lining
(the armholes are cut deep on the shop's mannequin), traced as white strips in the navy. The white body is
one piece; any white piece apart from it is lining, and goes navy.
    python car_back_slivers.py   (work folder, after trace_clash.py)"""
import numpy as np
from PIL import Image
from scipy import ndimage as nd

fn = 'design_CAR_back.png'
a = np.array(Image.open(fn).convert('RGBA'))
WHITE = np.array([0xE6, 0xE7, 0xF0])
NAVY = np.array([0x29, 0x2B, 0x36])
white = (np.abs(a[..., :3].astype(int) - WHITE).sum(-1) < 120) & (a[..., 3] > 0)
lab, n = nd.label(white)
sizes = nd.sum(white, lab, range(1, n + 1))
body = 1 + int(np.argmax(sizes))
lining = white & (lab != body)
lining = nd.binary_dilation(lining, iterations=2) & (a[..., 3] > 0) & (lab != body)
a[lining, :3] = NAVY
Image.fromarray(a).save(fn)
print('car back lining slivers', int(lining.sum()), 'px, pieces', n - 1)
