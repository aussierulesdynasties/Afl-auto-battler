# texture board: photo crop (reference only) | hand-painted map tiled 2x2 | name, painter family, grey stddev
import sys
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]
PAIRS = [('cream_boards', 'g22', (800, 2900, 2000, 3300)), ('glass', 'g22', (3200, 1250, 4400, 1650)),
         ('pavers', 'g23', (0, 3300, 1500, 3800)), ('concrete', 'g23', (4700, 2650, 5900, 3250)),
         ('seat_navy', 'g33', (480, 540, 760, 690)), ('seat_white', 'g23', (3500, 1850, 4600, 2250)),
         ('seat_timber', 'g39', (3150, 900, 3716, 1650)), ('asphalt', 'g39', (1200, 1050, 2400, 1350)),
         ('limestone', 'g36', (1100, 1150, 1400, 1350)), ('red_brick', 'g39', (2725, 940, 3040, 1150)),
         ('roof_zinc_pav', 'g36', (1350, 620, 1750, 800)), ('solar', 'sat', (0, -112, 30, -95))]
SD = {l.split()[0]: l.split()[1:3] for l in open('tex/stddev.txt') if l.strip()}
H = 220; W = 1100
try: F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
except Exception: F = None
board = Image.new('RGB', (W, H * len(PAIRS)), (24, 24, 24)); d = ImageDraw.Draw(board)
for i, (mat, ph, box) in enumerate(PAIRS):
    y = i * H
    if ph == 'sat':
        sys.path.insert(0, 'work'); import satm; a = satm.crop(*box, 19, 10).convert('RGB')
    else:
        a = Image.open(f'hunt/{ph}.jpg').convert('RGB').crop(box)
    a.thumbnail((420, H - 10)); board.paste(a, (5, y + 5))
    t = Image.open(f'tex/{mat}.png').convert('RGB').resize((H // 2 - 5, H // 2 - 5))
    for k in range(4): board.paste(t, (440 + (k % 2) * (H // 2 - 5), y + 5 + (k // 2) * (H // 2 - 5)))
    sd, fam = SD.get(mat, ['?', '?'])
    d.text((440 + H + 20, y + 30), f'{mat}', fill=(255, 255, 255), font=F)
    d.text((440 + H + 20, y + 70), f'painter: {fam}', fill=(200, 200, 200), font=F)
    d.text((440 + H + 20, y + 110), f'grey stddev {sd}', fill=(200, 255, 200), font=F)
    d.text((440 + H + 20, y + 150), (f'photo crop {ph} (reference only)' if ph != 'sat' else 'satellite crop (reference only)'), fill=(160, 160, 160), font=F)
board.save(out, quality=88); print(out, board.size)
