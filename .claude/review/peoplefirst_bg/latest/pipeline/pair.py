# aerial | model top view side by side for a world box, with a 20 m grid labelled in world metres
import sys
from PIL import Image, ImageDraw
x0, x1, y0, y1 = [int(v) for v in sys.argv[1:5]]; out = sys.argv[5]; k = float(sys.argv[6]) if len(sys.argv) > 6 else 2
s = Image.open('out/peoplefirst/ov/sat1400.png').convert('RGB').resize((1400, 1400), Image.BOX); t = Image.open('out/peoplefirst/ortho/top.png').convert('RGB')
b = (x0 + 700, 700 - y1, x1 + 700, 700 - y0); W, H = int((x1 - x0) * k), int((y1 - y0) * k)
w = Image.new('RGB', (2 * W + 8, H))
for i, im in enumerate((s, t)):
    c = im.crop(b).resize((W, H)); d = ImageDraw.Draw(c)
    for x in range(x0 - x0 % 20 + 20, x1, 20): d.line([((x - x0) * k, 0), ((x - x0) * k, H)], fill=(255, 255, 0) if x % 100 == 0 else (90, 90, 0)); d.text(((x - x0) * k + 2, 2), str(x), fill=(255, 255, 0))
    for y in range(y0 - y0 % 20 + 20, y1, 20): d.line([(0, (y1 - y) * k), (W, (y1 - y) * k)], fill=(255, 255, 0) if y % 100 == 0 else (90, 90, 0)); d.text((2, (y1 - y) * k + 2), str(y), fill=(255, 255, 0))
    w.paste(c, (i * (W + 8), 0))
w.save(out)
