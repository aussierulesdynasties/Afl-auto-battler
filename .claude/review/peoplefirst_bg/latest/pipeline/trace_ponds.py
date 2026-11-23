# aerial-only water blobs (reference trace): print blob id, area, world bbox; draw them over the aerial for eyeballing
from PIL import Image, ImageDraw
import numpy as np, json
from scipy import ndimage
exec(open('meas_water.py').read().split('inter=')[0])
miss = ws & ~ndimage.binary_dilation(wm, iterations=4)
lab, n = ndimage.label(miss)
im = Image.fromarray(s.astype(np.uint8)); d = ImageDraw.Draw(im)
out = []
for i, sl in enumerate(ndimage.find_objects(lab), 1):
    m = lab[sl] == i; A = m.sum()
    if A < 300: continue
    fill = A / m.size
    y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
    d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=2); d.text((x0, y0 - 10), str(i), fill=(255, 255, 0))
    out.append((i, int(A), round(fill, 2), (x0 - 700, x1 - 700, 700 - y1, 700 - y0)))
for o in out: print(o)
im.save('out/peoplefirst/ov/ponds_cand.png')
np.save('out/peoplefirst/ov/miss_lab.npy', lab)
