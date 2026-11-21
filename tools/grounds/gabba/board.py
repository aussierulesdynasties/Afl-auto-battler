# board.py TAG : full-res photo | render | 50% overlay, and a per-part crop board (photo crop over render crop)
import sys, json
from PIL import Image, ImageDraw
t = sys.argv[1]
ph = Image.open('refs/g49.jpg').convert('RGB'); r = Image.open(t + '_model.png').convert('RGB'); ov = Image.open(t + '_ov.png').convert('RGB')
W, H = ph.size; B = Image.new('RGB', (W * 3 + 40, H + 60), (20, 20, 22)); d = ImageDraw.Draw(B)
for i, (im, lab) in enumerate([(ph, 'photo (skyepics 100896-16796-021, 2022-07-14)'), (r, 'model, matched camera'), (Image.blend(ph, r, 0.5), '50% overlay')]):
    B.paste(im, (i * (W + 20), 60)); d.text((i * (W + 20) + 10, 20), lab, fill=(255, 255, 255))
B.save(t + '_board_full.png')
parts = json.load(open('parts_boxes.json'))
cells = []
for name, (x0, y0, x1, y1) in parts.items():
    s = 360 / max(x1 - x0, y1 - y0)
    sz = (int((x1 - x0) * s), int((y1 - y0) * s))
    a = ph.crop((x0, y0, x1, y1)).resize(sz, Image.LANCZOS); b = r.crop((x0, y0, x1, y1)).resize(sz, Image.LANCZOS)
    c = Image.new('RGB', (sz[0] * 2 + 30, sz[1] + 30), (20, 20, 22)); c.paste(a, (0, 30)); c.paste(b, (sz[0] + 30, 30))
    ImageDraw.Draw(c).text((4, 8), name + ': photo | model', fill=(255, 255, 255)); cells.append(c)
cw = max(c.width for c in cells); ch = max(c.height for c in cells); n = 2
G = Image.new('RGB', (cw * n + 20, ch * ((len(cells) + 1) // n) + 20), (20, 20, 22))
for i, c in enumerate(cells): G.paste(c, ((i % n) * (cw + 20), (i // n) * (ch + 20)))
G.save(t + '_parts.png'); print('ok', B.size, G.size)
