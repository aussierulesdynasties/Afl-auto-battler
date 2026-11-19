# col_post.py: COL front, the crest's gold laurels and 1892 banner (photo pixels with colour in them) drawn gold;
# trace.py snaps everything to the black and white of the stripes.
import numpy as np
from PIL import Image
d = np.array(Image.open('design_COL_front.png').convert('RGBA'))
p = np.array(Image.open('ref/COL_front.png').convert('RGB')).astype(int)
y0, y1, x0, x1 = 460, 600, 1100, 1215
b = p[y0:y1, x0:x1]; m = ((b.max(2) - b.min(2)) > 40) & (d[y0:y1, x0:x1, 3] > 0)
d[y0:y1, x0:x1, :3][m] = (0xC8, 0xC3, 0x82)
Image.fromarray(d).save('design_COL_front.png'); print('col_post gold', int(m.sum()))
