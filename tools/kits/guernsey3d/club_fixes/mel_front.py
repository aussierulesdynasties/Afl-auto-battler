# Melbourne front: the red V and the navy are mirror images about the centre (x 1000). The right half carries Zurich
# and the jock tag; it is rebuilt as the mirror of the left, then the MFC monogram (the club's emblem, kept) is put
# back from the photo.
import numpy as np
from PIL import Image
p = 'ref/MEL_front.png'
a = np.array(Image.open(p).convert('RGB'))
out = a.copy()
out[:, 1000:] = a[:, :1000][:, ::-1]
y0, y1, x0, x1 = 1495, 1585, 1265, 1340
out[y0:y1, x0:x1] = a[y0:y1, x0:x1]
Image.fromarray(out).save(p)
print('MEL front: right half mirrored, monogram kept')
