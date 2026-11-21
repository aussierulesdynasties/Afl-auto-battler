# Zoomed tierstrip of the photo only: bearing b0..b1 at 50 px/deg, z from z0 to z1, faint line every 1 deg, label every 1.
# python work/stripzoom.py view b0 b1 z0 z1 out.png
import sys, os, subprocess
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
v, b0, b1, z0, z1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
PX = 50
subprocess.run([sys.executable, os.path.join(HERE, 'tierstrip.py'), v, str(b0), str(b1), out + '.s.png', str(PX)], check=True, capture_output=True)
S = Image.open(out + '.s.png'); hh = (S.height - 4) // 2
for half, tag in ((0, 'p'), (1, 'r')):
    im = S.crop((0, half * (hh + 4) + int((31 - z1) * 10), S.width, half * (hh + 4) + int((31 - z0) * 10))).resize((S.width, int((z1 - z0) * 20)))
    dr = ImageDraw.Draw(im)
    import math
    for k in range(math.ceil(b0 * 2), int(b1 * 2) + 1):
        b = k / 2; x = (b - b0) * PX; full = k % 2 == 0
        dr.line([(x, 0), (x, 8 if not full else 14)], fill=(255, 0, 255)); 
        if full: dr.text((x + 2, 12), '%g' % (b % 360), fill=(255, 255, 0))
    for z in range(math.ceil(z0), int(z1) + 1):
        y = (z1 - z) * 20; dr.line([(0, y), (6, y)], fill=(0, 255, 255)); dr.text((8, y - 5), str(z), fill=(0, 255, 255))
    im.save(out.replace('.png', '_%s.png' % tag))
print(out)
