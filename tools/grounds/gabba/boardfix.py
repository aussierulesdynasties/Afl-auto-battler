# Gate-fault board: each fix beside the g49 crop the director named, plus the new textures beside their photo crop.
from PIL import Image, ImageDraw
ph = Image.open('refs/g49.jpg').convert('RGB')
def fit(im, h): return im.resize((round(im.size[0] * h / im.size[1]), h), Image.LANCZOS)
rows = [('1. Gate 7 block: navy, maroon strip at the bottom. Model (left) | photo g49 (330, 900, 450, 1000) (right)',
         fit(Image.open('cu_gate7ne.png').crop((440, 220, 940, 560)), 300), fit(ph.crop((330, 900, 450, 1000)), 300)),
        ('2. Fan building round drums. Model (left) | photo g49 (290, 860, 420, 950) (right)',
         fit(Image.open('cu_fans.png').crop((520, 230, 900, 470)), 300), fit(ph.crop((290, 860, 420, 950)), 300)),
        ('2b. Same drums from the east, low', fit(Image.open('cu_fans_low.png'), 300), None),
        ('Textures: n7front (Vulture St face) and n7strip (NE face), hand-painted | photo g49 (360, 940, 420, 1000)',
         fit(Image.open('htex/n7front.png'), 300), fit(Image.open('htex/n7strip.png'), 300), fit(ph.crop((360, 940, 420, 1000)), 300))]
W = 1500; H = sum(330 for _ in rows) + 10
b = Image.new('RGB', (W, H), (30, 30, 30)); d = ImageDraw.Draw(b); y = 6
for r in rows:
    d.text((10, y), r[0], fill=(240, 240, 240)); x = 10
    for im in r[1:]:
        if im is None: continue
        b.paste(im, (x, y + 22)); x += im.size[0] + 20
    y += 330
b.save('board_faults.png'); print(b.size)
