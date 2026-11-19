# proof.py OUTDIR: photo | render | 50% overlay at full resolution, plus per-part crop boards (photo | render | overlay)
import sys, os
from PIL import Image, ImageDraw
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
ph = Image.open('ref46.jpg').convert('RGB'); W, H = ph.size
r = Image.open('render46.png').convert('RGBA').resize((W, H))
bg = ph.copy().convert('RGBA'); bg.alpha_composite(r); ren = bg.convert('RGB')  # model over the photo's surroundings
rn = Image.new('RGBA', (W, H), (40, 40, 40, 255)); rn.alpha_composite(r); rn = rn.convert('RGB')  # model alone
ov = Image.blend(ph, rn, 0.5)


def lab(im, t):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 12 + 7 * len(t), 22], fill=(0, 0, 0)); d.text((6, 5), t, fill=(255, 255, 255)); return im


b = Image.new('RGB', (W * 3, H))
for i, (im, t) in enumerate([(ph, 'PHOTO ref46 (NAA A6135 K18/4/90/46)'), (rn, 'MODEL render, same camera'), (ov, '50% OVERLAY')]):
    b.paste(lab(im.copy(), t), (i * W, 0))
b.save(os.path.join(out, 'bruce_vs_photo.png'))
# second camera (ref50), the same sheet
p5 = Image.open('ref50.jpg').convert('RGB'); W5, H5 = p5.size
r5 = Image.open('render50.png').convert('RGBA').resize((W5, H5))
n5 = Image.new('RGBA', (W5, H5), (40, 40, 40, 255)); n5.alpha_composite(r5); n5 = n5.convert('RGB')
b5 = Image.new('RGB', (W5 * 3, H5))
for i, (im, t) in enumerate([(p5, 'PHOTO ref50 (second NAA frame)'), (n5, 'MODEL render, same camera'), (Image.blend(p5, n5, 0.5), '50% OVERLAY')]):
    b5.paste(lab(im.copy(), t), (i * W5, 0))
b5.save(os.path.join(out, 'bruce_vs_photo50.png'))
PARTS = {'north_bowl': (700, 270, 1200, 470), 'east_bowl': (1250, 300, 1560, 760), 'west_bowl': (430, 420, 760, 800),
         'main_stand_roof': (860, 700, 1700, 960), 'stand_facade': (880, 840, 1520, 1000), 'light_towers': (380, 250, 1560, 1060),
         'scoreboard': (1460, 560, 1620, 700), 'stand_ends_gates': (820, 800, 1000, 1000), 'concourse': (440, 280, 900, 760)}
for k, (x0, y0, x1, y1) in PARTS.items():
    s = max(1, int(1200 / (x1 - x0)))
    tiles = [lab(im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * s, (y1 - y0) * s), Image.LANCZOS), t)
             for im, t in [(ph, 'photo'), (rn, 'model'), (ov, 'overlay')]]
    w, h = tiles[0].size; bb = Image.new('RGB', (w, h * 3 + 8), (255, 255, 255))
    for i, t in enumerate(tiles): bb.paste(t, (0, i * (h + 4)))
    bb.save(os.path.join(out, 'board_%s.png' % k))
print('ok')
