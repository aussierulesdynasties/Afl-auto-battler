# python work/gridcrop.py v x0,y0,x1,y1 scale out [step] : GE crop with a labelled full-frame pixel grid (for picking points)
import sys
from PIL import Image, ImageDraw
v = sys.argv[1]; x0, y0, x1, y1 = (int(t) for t in sys.argv[2].split(',')); sc = float(sys.argv[3]); out = sys.argv[4]
st = int(sys.argv[5]) if len(sys.argv) > 5 else 20
src = sys.argv[6] if len(sys.argv) > 6 else f'ge/{v}.png'
im = Image.open(src).convert('RGB').crop((x0, y0, x1, y1)).resize((int((x1 - x0) * sc), int((y1 - y0) * sc)), Image.LANCZOS)
d = ImageDraw.Draw(im)
for x in range((x0 // st + 1) * st, x1, st):
    X = (x - x0) * sc; big = x % (st * 5) == 0
    d.line([(X, 0), (X, im.size[1])], fill=(255, 255, 0) if big else (255, 255, 0, 60), width=1 if not big else 2)
    if big: d.text((X + 2, 2), str(x), fill=(255, 255, 0))
for y in range((y0 // st + 1) * st, y1, st):
    Y = (y - y0) * sc; big = y % (st * 5) == 0
    d.line([(0, Y), (im.size[0], Y)], fill=(255, 255, 0), width=2 if big else 1)
    if big: d.text((2, Y + 2), str(y), fill=(255, 255, 0))
im.save(out, quality=90); print(out, im.size)
