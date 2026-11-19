# texture board: each hand-made texture beside a crop of the same surface in a reference photo, plus grey stddev
import sys, json, numpy as np
sys.path.insert(0, '.')
import aerial90 as A
from PIL import Image, ImageDraw, ImageStat
out = sys.argv[1]
S90 = Image.open('check90/src90.png').convert('RGB'); R46 = Image.open('ref46.jpg').convert('RGB')
def c90(b, g, m=12.0):
    t = np.radians(b); r = A.r_grass(t)[0] + g
    x, y = A.m2px(np.array([[A.CX + r * np.cos(t), A.CY + r * np.sin(t)]]))[0]; h = m / 0.25 / 2
    return S90.crop((int(x - h), int(y - h), int(x + h), int(y + h)))
def c46(x, y, h): return R46.crop((x - h, y - h, x + h, y + h))
R50 = Image.open('ref50.jpg').convert('RGB')
def c50(x, y, h): return R50.crop((x - h, y - h, x + h, y + h))
ROWS = [('seats', 'seats', lambda: c90(-30, 25), '1990 vertical, SE seats'),
        ('grassbank', 'grass bank', lambda: c90(20, 8, 6), '1990 vertical, E bank'),
        ('concrete', 'rim walkway', lambda: c90(-110, 21.5, 8), '1990 vertical, S rim'),
        ('gravel', 'gravel', lambda: c90(-95, 30), '1990 vertical, S gravel'),
        ('path', 'path', lambda: c90(-100, 35.5, 8), '1990 vertical, S path'),
        ('lawn', 'lawn', lambda: c90(-122, 28), '1990 vertical, SW lawn'),
        ('roof', 'stand roof', lambda: c46(1150, 830, 35), 'ref46, stand roof'),
        ('facade', 'stand facade', lambda: c46(1120, 915, 60), 'ref46, stand front'),
        ('tower', 'light tower', lambda: c50(1561, 655, 22), 'ref50, east tower mast'),
        ('wall', 'outer wall', lambda: c50(1544, 790, 18), 'ref50, bowl back edge (wall face hidden from above)')]
T = 256; W = T * 2 + 30; H = T + 34
B = Image.new('RGB', (W * 2, H * ((len(ROWS) + 1) // 2) + 30), (24, 24, 24)); d = ImageDraw.Draw(B)
d.text((8, 8), 'Bruce Stadium 1990: hand-made texture (left) beside the photo (right); grey stddev of the texture', fill=(255, 255, 255))
for k, (tex, name, crop, src) in enumerate(ROWS):
    im = Image.open('tex/%s.png' % tex).convert('RGB'); sd = ImageStat.Stat(im.convert('L')).stddev[0]
    x0 = (k % 2) * W; y0 = 30 + (k // 2) * H
    B.paste(im.resize((T, T)), (x0 + 10, y0 + 24)); B.paste(crop().resize((T, T), Image.LANCZOS), (x0 + T + 20, y0 + 24))
    d.text((x0 + 10, y0 + 6), '%s  tex/%s.png  stddev %.1f' % (name, tex, sd), fill=(255, 230, 0)); d.text((x0 + T + 20, y0 + 6), src, fill=(180, 220, 255))
B.save(out)
with open(out.replace('.png', '_stddev.txt'), 'w', encoding='utf-8', newline='\n') as f:
    for p in sorted(json.load(open('tex/index.json'))):
        try: f.write('%-12s %.1f\n' % (p, ImageStat.Stat(Image.open('tex/%s.png' % p).convert('L')).stddev[0]))
        except FileNotFoundError: pass
print(open(out.replace('.png', '_stddev.txt')).read())
