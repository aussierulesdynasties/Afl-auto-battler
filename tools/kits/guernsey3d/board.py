"""photo | our model (matched camera) | 50% overlay, front and back.
Camera: 800x1100, 0.62 m across at 6 m, aimed at y 1.30 -> 1290 px a metre on screen.
Photo: row 189 = y 1.62, 2310 px a metre (the cut's own projection)."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
code, cap, out = sys.argv[1], sys.argv[2], sys.argv[3]
SPX, CPX = 2310.0, 800 / 0.62 * 6.0 / 5.88   # surface ~12 cm nearer the camera than the aim point
s = CPX / SPX
rows = []
f = ImageFont.truetype('arial.ttf', 26)
for side in ('front', 'back'):
    al = np.array(Image.open(f'design_{code}_{side}.png'))[..., 3] > 127
    r = al[860]; nz = np.nonzero(r)[0]; cx = (nz.min() + nz.max()) / 2
    ph = Image.open(f'ref/{code}_{side}.png').convert('RGB')
    # screen = s * photo + t
    tx = 400 - cx * s
    ty = 550 - (1.30 - 1.62) * CPX * -1 - 189 * s
    ty = 550 - (1.62 - 1.30) * CPX - 189 * s
    inv = (1 / s, 0, -tx / s, 0, 1 / s, -ty / s)
    warped = ph.transform((800, 1100), Image.AFFINE, inv, resample=Image.BICUBIC, fillcolor=(255, 255, 255))
    rend = Image.open(f'{cap}/{code}_{side}.png').convert('RGB')
    blend = Image.blend(warped, rend, 0.5)
    row = Image.new('RGB', (2400, 1140), 'white')
    for i, (im, lab) in enumerate([(warped, f'{side}: photo'), (rend, f'{side}: our model'), (blend, f'{side}: 50% overlay')]):
        row.paste(im, (i * 800, 40))
        ImageDraw.Draw(row).text((i * 800 + 12, 6), lab, fill='black', font=f)
    rows.append(row)
b = Image.new('RGB', (2400, 2280), 'white')
b.paste(rows[0], (0, 0)); b.paste(rows[1], (0, 1140))
b.save(out)
b.resize((1200, 1140)).save(out.replace('.png', '_small.png'))
