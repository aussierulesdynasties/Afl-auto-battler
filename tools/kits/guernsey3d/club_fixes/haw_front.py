# Hawthorn front: the stripes are mirror images about the centre (x 1000), and the sponsors sit on solid panels that
# break them (Tasmanian on a brown block over the right gold stripe, the jock tag low on the right). The right half is
# rebuilt as the mirror of the left, then the Hawks crest (the club's emblem, kept) is put back from the photo.
import numpy as np
from PIL import Image
p = 'ref/HAW_front.png'
a = np.array(Image.open(p).convert('RGB'))
out = a.copy()
out[:, 1000:] = a[:, :1000][:, ::-1]
y0, y1, x0, x1 = 705, 880, 1085, 1225
out[y0:y1, x0:x1] = a[y0:y1, x0:x1]
Image.fromarray(out).save(p)
print('HAW front: right half mirrored, crest kept')
