# proof set: python w/proof.py V PHOTO RENDER OUTDIR parts.json
# writes V_overlay.png (photo | render on photo | 50% blend, full res) and V_part_<name>.png per part box
import sys, json, os
from PIL import Image
V, photo, rend, outd, partsj = sys.argv[1:6]
R = Image.open(rend).convert('RGBA')
P = Image.open(photo).convert('RGBA').resize(R.size, Image.LANCZOS)
O = P.copy(); O.alpha_composite(R)
M = Image.blend(P, O, 0.5)
w, h = R.size
B = Image.new('RGB', (w * 3, h))
for i, im in enumerate([P, O, M]):
    B.paste(im.convert('RGB'), (i * w, 0))
os.makedirs(outd, exist_ok=True)
B.save(os.path.join(outd, f'{V}_overlay.png'))
for name, box in json.load(open(partsj)).items():
    a, b, m = P.crop(box), O.crop(box), M.crop(box)
    pw, ph = a.size
    s = max(1, 900 // ph) if ph < 900 else 1
    C = Image.new('RGB', (pw * 3 * s + 20, ph * s), (255, 255, 255))
    for i, im in enumerate([a, b, m]):
        C.paste(im.convert('RGB').resize((pw * s, ph * s), Image.LANCZOS), (i * (pw * s + 10), 0))
    C.save(os.path.join(outd, f'{V}_part_{name}.png'))
print('ok', V)
