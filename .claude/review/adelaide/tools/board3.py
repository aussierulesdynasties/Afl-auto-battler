"""board3.py PHOTO RENDER OUT [x0,y0,x1,y1]: photo | render | 50% overlay, full resolution, side by side"""
import sys
from PIL import Image
ph = Image.open(sys.argv[1]).convert('RGBA'); r = Image.open(sys.argv[2]).convert('RGBA')
if r.size != ph.size: r = r.resize(ph.size)  # camera C renders the pano's cylinder at 2062 rows; stretched back as cmpC.py did
sky = Image.new('RGBA', ph.size, (40, 40, 40, 255)); rr = Image.alpha_composite(sky, r)
bl = Image.blend(ph, Image.alpha_composite(ph, r), 0.5)
ims = [ph, rr, bl]
if len(sys.argv) > 4: c = [int(v) for v in sys.argv[4].split(',')]; ims = [i.crop(c) for i in ims]
W, H = ims[0].size; out = Image.new('RGB', (W * 3 + 40, H), (0, 0, 0))
for k, i in enumerate(ims): out.paste(i.convert('RGB'), (k * (W + 20), 0))
out.save(sys.argv[3], quality=92)
