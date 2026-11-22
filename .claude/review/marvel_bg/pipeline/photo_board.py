"""photo | render | 50/50 board for the photo-matched cameras. python photo_board.py out.jpg"""
import sys
from PIL import Image, ImageDraw
R = 'D:/Temp/claude/534e6ed5702e321f/e26221bc-b0d7-453b-b6bd-aa7897b49bd3/scratchpad/'
rows = []
for p in ['p3', 'p4', 'p5']:
    b = Image.open(R + 'proto/out/marvel/photo/' + p + '.png').convert('RGB'); a = Image.open(R + 'ref_mv/' + p + '.jpg').resize(b.size)
    s = Image.new('RGB', (b.size[0] * 3, b.size[1]))
    for k, im in enumerate([a, b, Image.blend(a, b, 0.5)]): s.paste(im, (k * b.size[0], 0))
    ImageDraw.Draw(s).text((8, 8), p + ': photo | render | 50/50', fill=(255, 255, 0))
    rows.append(s.resize((1800, int(1800 * s.size[1] / s.size[0]))))
o = Image.new('RGB', (1800, sum(r.size[1] for r in rows))); y = 0
for r in rows: o.paste(r, (0, y)); y += r.size[1]
o.save(sys.argv[1], quality=88)
