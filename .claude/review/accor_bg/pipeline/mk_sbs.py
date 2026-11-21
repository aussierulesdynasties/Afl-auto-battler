import sys, os
from PIL import Image, ImageDraw
# usage: mk_sbs.py out.jpg render.png photo.jpg [render photo ...]
out = sys.argv[1]; pairs = list(zip(sys.argv[2::2], sys.argv[3::2])); H = 360; rows = []
for r, p in pairs:
    a = Image.open(r).convert('RGB'); b = Image.open(p).convert('RGB')
    a = a.resize((int(a.width * H / a.height), H)); b = b.resize((int(b.width * H / b.height), H))
    row = Image.new('RGB', (a.width + b.width + 10, H + 24), (20, 20, 20)); row.paste(a, (0, 24)); row.paste(b, (a.width + 10, 24))
    d = ImageDraw.Draw(row); d.text((4, 4), 'RENDER ' + os.path.basename(r), fill=(255, 255, 0)); d.text((a.width + 14, 4), 'PHOTO ' + os.path.basename(p), fill=(255, 255, 0))
    rows.append(row)
W = max(r.width for r in rows); im = Image.new('RGB', (W, sum(r.height for r in rows)), (20, 20, 20)); y = 0
for r in rows: im.paste(r, (0, y)); y += r.height
im.save(out, quality=88); print(out, im.size)
