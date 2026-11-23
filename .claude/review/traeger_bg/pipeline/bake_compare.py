import os
import numpy as np
from PIL import Image, ImageDraw
H = os.path.dirname(os.path.abspath(__file__)); O = os.path.join(H, 'out', 'mcg')
names = ['base_%03d' % i for i in range(4)] + ['ring_%03d' % i for i in range(4)]
W, Hh = 960, 540
sheet = Image.new('RGB', (2 * W, len(names) * Hh), 'black'); d = ImageDraw.Draw(sheet)
for r, n in enumerate(names):
    a = Image.open(os.path.join(O, 'check_prebake', n + '.png')).convert('RGB')
    b = Image.open(os.path.join(O, 'check', n + '.png')).convert('RGB')
    diff = np.abs(np.asarray(a, np.float32) - np.asarray(b, np.float32)).mean()
    print(n, 'mean abs diff %.2f' % diff)
    sheet.paste(a.resize((W, Hh)), (0, r * Hh)); sheet.paste(b.resize((W, Hh)), (W, r * Hh))
    d.text((10, r * Hh + 10), n + ' before', fill='yellow'); d.text((W + 10, r * Hh + 10), n + ' after  diff %.2f' % diff, fill='yellow')
sheet.save(os.path.join(O, 'bake_compare.jpg'), quality=88)
