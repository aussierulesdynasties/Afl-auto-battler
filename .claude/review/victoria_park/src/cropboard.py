# cropboard.py OUTDIR : per-part PHOTO | RENDER | 50% crops at full reference resolution
import sys, os
from PIL import Image, ImageDraw, ImageFont
O = sys.argv[1]
ph = Image.open('ref_full.png').convert('RGB'); rn = Image.open(os.path.join(O, 'render_full.png')).convert('RGB')
ov = Image.open(os.path.join(O, 'overlay50_full.png')).convert('RGB')
PARTS = {'Sherrin stand': (1350, 200, 1950, 1050), 'Social Club': (1050, 900, 1550, 1250),
         'Ryder stand': (350, 850, 1100, 1200), 'Rush stand': (500, 150, 1700, 520), 'West end terraces': (0, 300, 500, 1000)}
f = ImageFont.truetype('arial.ttf', 28)
rows = []
for nm, box in PARTS.items():
    w, h = box[2] - box[0], box[3] - box[1]; s = 600 / max(w, h)
    ims = [im.crop(box).resize((int(w * s), int(h * s)), Image.LANCZOS) for im in (ph, rn, ov)]
    r = Image.new('RGB', (3 * 610, ims[0].height + 40), (20, 20, 24)); d = ImageDraw.Draw(r)
    for i, im in enumerate(ims): r.paste(im, (i * 610, 40))
    d.text((5, 5), nm + ': photo | model | 50%', fill=(240, 240, 240), font=f); rows.append(r)
H = sum(r.height for r in rows); B = Image.new('RGB', (3 * 610, H)); y = 0
for r in rows: B.paste(r, (0, y)); y += r.height
B.save(os.path.join(O, 'crop_board.png')); print('ok', B.size)
