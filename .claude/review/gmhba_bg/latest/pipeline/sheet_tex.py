"""Contact sheet of textures (alpha shown over sky blue). sheet_tex.py out.png tex1.png ..."""
import sys, os
from PIL import Image, ImageDraw
out, fs = sys.argv[1], sys.argv[2:]; S = 300
sh = Image.new('RGB', (S * 4, (S + 20) * ((len(fs) + 3) // 4)), (40, 40, 40)); d = ImageDraw.Draw(sh)
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGBA'); bg = Image.new('RGBA', im.size, (90, 140, 200, 255)); im = Image.alpha_composite(bg, im).convert('RGB')
    im.thumbnail((S, S)); x, y = (i % 4) * S, (i // 4) * (S + 20)
    sh.paste(im, (x, y + 20)); d.text((x + 4, y + 4), os.path.basename(f), fill=(255, 255, 255))
sh.save(out)
