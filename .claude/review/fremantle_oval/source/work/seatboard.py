# seat board: photo crop (reference only) beside the model seat close-up. usage: seatboard.py <proof dir> <out>
import sys
from PIL import Image, ImageDraw, ImageFont
P, out = sys.argv[1], sys.argv[2]
ROWS = [('North stand navy seats', 'g33', (480, 540, 760, 690), 'seat_nstand'),
        ('Pavilion timber plank benches', 'g39', (3150, 900, 3716, 1650), 'seat_pav')]
F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22); H = 520; W = 1500
b = Image.new('RGB', (W, (H + 40) * len(ROWS)), (24, 24, 24)); d = ImageDraw.Draw(b)
for i, (n, ph, box, sh) in enumerate(ROWS):
    y = i * (H + 40); d.text((10, y + 8), f'{n}   |   left: photo {ph} (reference only)   right: model, shot {sh}', fill=(255, 255, 255), font=F)
    a = Image.open(f'hunt/{ph}.jpg').convert('RGB').crop(box); a.thumbnail((560, H)); b.paste(a, (10, y + 40))
    r = Image.open(f'{P}/{sh}.png').convert('RGB'); r.thumbnail((W - 600, H)); b.paste(r, (590, y + 40))
b.save(out, quality=88); print(out, b.size)
