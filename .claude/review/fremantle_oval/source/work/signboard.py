# sign board: each hand-made sign in the model beside its reference photo crop. usage: signboard.py <proof dir> <out>
import sys
from PIL import Image, ImageDraw, ImageFont
P, out = sys.argv[1], sys.argv[2]
ROWS = [('North stand name sign', 'g33', (545, 410, 990, 550), 'close_nstand'),
        ('SOUTH FREMANTLE FOOTBALL CLUB fascia', 'g23', (0, 650, 6022, 1555), 'gj_fascia'),
        ('BULLDOGS badge and mural', 'g12', (850, 170, 1155, 530), 'gj_nw'),
        ('George Grljusich Media Box sign', 'g22', (2100, 2850, 3450, 3200), 'media_oval'),
        ('WISH YOU WERE HERE gate (2024)', 'a04', (1350, 1740, 1760, 1880), 'close_gate')]
H = 300; W = 1400
try: F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
except Exception: F = None
board = Image.new('RGB', (W, (H + 40) * len(ROWS)), (24, 24, 24)); d = ImageDraw.Draw(board)
for i, (name, ph, box, shot) in enumerate(ROWS):
    y = i * (H + 40)
    d.text((10, y + 8), f'{name}   |   left: photo {ph} (reference only)   right: model, shot {shot}', fill=(255, 255, 255), font=F)
    a = Image.open(f'hunt/{ph}.jpg').convert('RGB').crop(box); a.thumbnail((560, H - 10)); board.paste(a, (10, y + 40))
    r = Image.open(f'{P}/{shot}.png').convert('RGB'); r.thumbnail((W - 600, H - 10)); board.paste(r, (590, y + 40))
board.save(out, quality=88); print(out, board.size)
