# photo | render crop board: python build/board.py photo render out "label"
import sys
from PIL import Image, ImageDraw
ph, rn, out, label = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
H = 720
a = Image.open(ph).convert('RGB'); b = Image.open(rn).convert('RGB')
a = a.resize((round(a.width * H / a.height), H), Image.LANCZOS)
b = b.resize((round(b.width * H / b.height), H), Image.LANCZOS)
im = Image.new('RGB', (a.width + b.width + 12, H + 40), (24, 24, 24))
im.paste(a, (0, 40)); im.paste(b, (a.width + 12, 40))
d = ImageDraw.Draw(im)
d.text((8, 12), 'PHOTO ' + label.split('|')[0], fill=(255, 255, 255))
d.text((a.width + 20, 12), 'RENDER ' + label.split('|')[1], fill=(255, 255, 255))
im.save(out, quality=92)
print(out, im.size)
