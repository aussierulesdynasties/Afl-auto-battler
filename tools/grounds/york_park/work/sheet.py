# python work/sheet.py "glob" out.jpg [cols] : contact sheet of renders (transparent background filled sky blue), file name on each
import sys, glob, os
from PIL import Image, ImageDraw
fs = sorted(glob.glob(sys.argv[1])); out = sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3; w = 640; h = w * 9 // 16
rows = (len(fs) + cols - 1) // cols; c = Image.new('RGB', (cols * w, rows * (h + 18)), (30, 30, 30)); d = ImageDraw.Draw(c)
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGBA'); bg = Image.new('RGBA', im.size, (140, 160, 190, 255)); bg.alpha_composite(im)
    x, y = (i % cols) * w, (i // cols) * (h + 18); c.paste(bg.convert('RGB').resize((w, h)), (x, y + 18)); d.text((x + 4, y + 3), os.path.basename(f), fill=(255, 255, 0))
c.save(out, quality=88)
