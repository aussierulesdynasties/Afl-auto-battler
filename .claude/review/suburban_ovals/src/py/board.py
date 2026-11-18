"""photo | render | 50% overlay board (+ a full-size overlay with the pixel grid)."""
import sys
from PIL import Image, ImageDraw, ImageFont
k, rp, out = sys.argv[1], sys.argv[2], sys.argv[3]
ph = Image.open("grid/%s_2000.png" % k).convert("RGB"); rd = Image.open(rp).convert("RGB").resize(ph.size)
ov = Image.blend(ph, rd, 0.5)
gr = Image.open("grid/%s_grid.jpg" % k).convert("RGB")
ovg = Image.blend(gr, rd, 0.5); ovg.save(out.replace(".jpg", "_ovgrid.jpg"), quality=88)
w = 900; h = round(ph.height * w / ph.width)
B = Image.new("RGB", (w * 3 + 40, h + 50), (24, 24, 26)); d = ImageDraw.Draw(B); f = ImageFont.truetype("arial.ttf", 22)
for i, (im, t) in enumerate(((ph, "photo"), (rd, "render"), (ov, "50% overlay"))):
    B.paste(im.resize((w, h), Image.LANCZOS), (10 + i * (w + 10), 40)); d.text((10 + i * (w + 10), 8), t, fill=(240, 240, 240), font=f)
B.save(out, quality=90)
