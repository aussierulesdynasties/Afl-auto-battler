"""Texture board: per surface, photo crop | model from game distance | model close, with grey-level stddev."""
from PIL import Image, ImageDraw, ImageFont
import re
SD = {}
for l in open('rend/tex/stats.txt'):
    p = l.split(); SD[p[0]] = (float(p[3]), float(p[6]))
PH = {}
for l in open('rend/s/photo_sd.txt'):
    p = l.split(); PH[p[0]] = float(p[3])
ROWS = [('seats', 'seats', 'seats', ['seats_red', 'seats_slate', 'seats_teal', 'seats_maroon', 'seats_navy']),
        ('membrane', 'membrane', 'membrane', ['membrane']),
        ('concrete', 'concrete', 'concrete', ['concrete_cream', 'concrete_grey', 'concrete_mid', 'concrete_slate', 'concrete_dark']),
        ('brick', 'concrete', 'concrete', ['brick', 'brick_red']),
        ('steel', 'steel', 'steel', ['steel_white', 'steel_pale', 'steel_grey']),
        ('hill_turf', 'hill', 'hill', ['hill_turf']),
        ('scoreboard', 'board', 'board', ['scoreboard'])]
W, H = 560, 315
try: F = ImageFont.truetype('arial.ttf', 18)
except Exception: F = ImageFont.load_default()
im = Image.new('RGB', (W * 3 + 20, (H + 70) * len(ROWS) + 40), (18, 18, 18)); d = ImageDraw.Draw(im)
d.text((10, 10), 'Adelaide Oval texture pass: photo crop | model at game distance | model close.  sd = grey-level stddev 0-255', fill=(255, 255, 0), font=F)
for i, (ph, far, near, mats) in enumerate(ROWS):
    y = 40 + i * (H + 70)
    a = Image.open(f'rend/s/ref_{ph}_big.jpg' if ph == 'steel' else f'rend/s/ref_{ph}.jpg').convert('RGB')
    k = min(W / a.width, H / a.height); a = a.resize((max(1, round(a.width * k)), max(1, round(a.height * k))), Image.LANCZOS); im.paste(a, (0, y))   # crop scaled up to fill its cell
    for j, f in enumerate((far, near)):
        b = Image.open(f'rend/s/{f}_{("far", "near")[j]}.png').convert('RGB').resize((W, H)); im.paste(b, ((j + 1) * (W + 10), y))
    s = '  '.join(f'{m} {SD[m][0]:.0f}/{SD[m][1]:.0f}' for m in mats if m in SD)
    d.text((0, y + H + 6), f'{ph}: photo sd {PH.get(ph, 0):.1f}' + ('  (sd of the bare fascia face; crop shows pale steel fascia and roof tubes)' if ph == 'steel' else ''), fill=(255, 255, 255), font=F)
    d.text((0, y + H + 32), f'model sd far/near: {s}', fill=(180, 220, 255), font=F)
im.save('rend/s/texboard.jpg', quality=88)
print(im.size)
