"""ref | render pairs, 2 per row. pair.py out.jpg ref1 ren1 ref2 ren2 ..."""
import sys
from PIL import Image
out, fs = sys.argv[1], sys.argv[2:]; H = 520
ims = []
for f in fs:
    im = Image.open(f).convert('RGB'); ims.append(im.resize((int(im.width * H / im.height), H)))
rows = [ims[i:i + 4] for i in range(0, len(ims), 4)]
W = max(sum(i.width for i in r) for r in rows)
sh = Image.new('RGB', (W + 30, H * len(rows)), (30, 30, 30))
for j, r in enumerate(rows):
    x = 0
    for k, im in enumerate(r): sh.paste(im, (x, j * H)); x += im.width + (30 if k == 1 else 0)
sh.save(out, quality=88)
