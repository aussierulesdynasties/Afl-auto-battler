"""Richmond clash, front: through the neck the photo shows the inside of the back collar (its black PUMA
tape), traced as two black slivers either side of the neck. On the front the cloth there is yellow; the
sash starts right of x 1180 (ref/RIC_front.png, the cut's square).
    python ric_front_neck.py   (work folder, after trace_clash.py)"""
import numpy as np
from PIL import Image

fn = 'design_RIC_front.png'
a = np.array(Image.open(fn).convert('RGBA'))
YELLOW = np.array([0xF5, 0xCA, 0x32])
BLACK = np.array([0x2B, 0x26, 0x26])
box = a[260:350, 760:1180]
dark = (np.abs(box[..., :3].astype(int) - BLACK).sum(-1) < 300) & (box[..., 3] > 0)
box[dark, :3] = YELLOW
Image.fromarray(a).save(fn)
print('ric front neck tape gone', int(dark.sum()), 'px')
