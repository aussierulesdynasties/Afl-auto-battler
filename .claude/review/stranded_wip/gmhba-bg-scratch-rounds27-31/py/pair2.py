import sys
from PIL import Image
ph, rd, out = sys.argv[1:4]
a = Image.open(ph).convert('RGB'); b = Image.open(rd).convert('RGB').resize(a.size)
m = Image.blend(a, b, 0.5)
W, H = a.size; s = Image.new('RGB', (W * 3, H)); [s.paste(x, (i * W, 0)) for i, x in enumerate((a, b, m))]
s.save(out, quality=90)
