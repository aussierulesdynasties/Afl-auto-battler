# wbd_design_fix.py: Western Bulldogs front, run after trace.py (it edits design_WBD_front.png in place).
# The front's F.F.C. is printed as thin white outlines (about 6 px in the frame) on the blue; trace.py fills and spikes
# strokes that thin (director 2026-11-19 on the hoops: "sloppy line work"). The design is in the photo's frame, so the
# letters' box (frame x 1045-1220, rows 572-655, blue all round its border) is redrawn straight from
# ref/WBD_front_photo.png: white (235,235,246) where the photo's darkest channel is above 128 after a 1 px blur, blue
# (0,53,156) elsewhere; white specks under 10 px dropped.
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, label
x0, y0, x1, y1 = 1045, 572, 1221, 656
p = np.asarray(Image.open('ref/WBD_front_photo.png').convert('RGB')).astype(float)[y0:y1, x0:x1]
m = gaussian_filter(p.min(-1), 1.0) > 128
lab, n = label(m); sz = np.bincount(lab.ravel()); m &= (sz >= 10)[lab]   # specks under 10 px are cloth noise
d = np.asarray(Image.open('design_WBD_front.png').convert('RGBA')).copy()
box = d[y0:y1, x0:x1]
box[..., :3] = (0, 53, 156); box[m, :3] = (235, 235, 246)
Image.fromarray(d).save('design_WBD_front.png')
print('F.F.C. redrawn: %d white px' % m.sum())
