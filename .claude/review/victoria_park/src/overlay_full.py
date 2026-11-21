# overlay_full.py RENDER OUTDIR : photo | render | 50% overlay at the reference's full size (2000x1355)
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ren = Image.open(sys.argv[1]).convert('RGBA'); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
ph = Image.open('ref_full.png').convert('RGBA'); FW, FH = ph.size
A = np.load('aff_small_to_full.npy')            # full = A @ [small, 1]
k = ren.size[0] / 747.0                          # render px per small px
s = A[0, 0] / k                                  # full px per render px
ox, oy = A[0, 2], A[1, 2]
# PIL wants the inverse map: render = (full - off) / s
r = ren.transform((FW, FH), Image.AFFINE, (1 / s, 0, -ox / s, 0, 1 / s, -oy / s), resample=Image.BICUBIC)
solid = Image.alpha_composite(Image.new('RGBA', (FW, FH), (30, 32, 36, 255)), r)
a = np.array(r).astype(float)
ov = Image.alpha_composite(ph, Image.fromarray(np.dstack([a[..., :3], a[..., 3] * 0.5]).astype(np.uint8)))
solid.convert('RGB').save(os.path.join(OUT, 'render_full.png'))
ov.convert('RGB').save(os.path.join(OUT, 'overlay50_full.png'))
try: f = ImageFont.truetype('arial.ttf', 40)
except Exception: f = ImageFont.load_default()
bg = Image.new('RGB', (FW * 3 + 40, FH + 70), (20, 20, 24)); d = ImageDraw.Draw(bg)
for i, (im, t) in enumerate(((ph, 'Photo (reference, 1990s, Austadiums)'), (solid, 'Model from the matched camera'),
                             (ov, 'Model at 50% over the photo'))):
    bg.paste(im.convert('RGB'), (10 + i * (FW + 10), 60)); d.text((10 + i * (FW + 10), 10), t, fill=(240, 240, 240), font=f)
bg.save(os.path.join(OUT, 'board_full.png'))
print('ok', FW, FH)
