# 4x2 contact sheet of the 8 PNGs in a folder -> <folder>/sheet.jpg
import sys, os, glob
from PIL import Image, ImageDraw
d = sys.argv[1]; fs = sorted(f for f in glob.glob(os.path.join(d, '*.png')))[:8]
w, h = 480, 270; S = Image.new('RGB', (4 * w, 2 * h), (20, 20, 20))
for k, f in enumerate(fs):
    im = Image.open(f).convert('RGB').resize((w, h), Image.LANCZOS); S.paste(im, ((k % 4) * w, (k // 4) * h))
    ImageDraw.Draw(S).text(((k % 4) * w + 6, (k // 4) * h + 4), os.path.basename(f), fill=(255, 255, 0))
S.save(os.path.join(d, 'sheet.jpg'), quality=90); print(d, len(fs))
