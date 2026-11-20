# Height rulers on a GE view: python work/ruler.py view out.png "b:r b:r ..." [crop x0,y0,x1,y1] [scale]
# Each ruler stands at plan point (bearing b, radius r), ticks every 2 m (long tick + label every 10 m), z = 0..40 above the field.
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gecam as G
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
v, out, spec = sys.argv[1], sys.argv[2], sys.argv[3]
im = Image.open(os.path.join(SP, 'ge', v + '.png')).convert('RGB'); d = ImageDraw.Draw(im)
cols = [(255, 0, 255), (0, 255, 255), (255, 255, 0), (255, 80, 80), (80, 255, 80)]
for i, s in enumerate(spec.split()):
    b, r = map(float, s.split(':')); a = math.radians(b); x, y = r * math.sin(a), r * math.cos(a); c = cols[i % len(cols)]
    q = G.P(v, [[x, y, z] for z in range(0, 41, 2)])
    d.line([tuple(q[0]), tuple(q[-1])], fill=c, width=1)
    for k, p in enumerate(q):
        L = 6 if (2 * k) % 10 == 0 else 3; d.line([(p[0] - L, p[1]), (p[0] + L, p[1])], fill=c, width=1)
        if (2 * k) % 10 == 0 and k: d.text((p[0] + 7, p[1] - 6), str(2 * k), fill=c)
    d.text((q[0][0] - 10, q[0][1] + 3), s, fill=c)
if len(sys.argv) > 4:
    im = im.crop(tuple(map(int, sys.argv[4].split(','))))
    if len(sys.argv) > 5: k = float(sys.argv[5]); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
im.save(out); print(out, im.size)
