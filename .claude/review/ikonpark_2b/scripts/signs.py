# hand-painted sign textures (font + flat colour), no photo pixels
# PLAIN=True: panels only, no lettering or roundels (lead 2026-11-18: sponsor lettering plain until the director picks)
PLAIN = True
import sys
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]
F = 'C:/Windows/Fonts/'
# Foster's roof sign: white border, sky-blue panel, gold-ringed roundels at each end, white serif letters outlined navy
W, H = 2400, 300
im = Image.new('RGB', (W, H), (245, 247, 248)); d = ImageDraw.Draw(im)
d.rectangle([14, 14, W - 15, H - 15], fill=(95, 160, 205))
for cx in (175, W - 175):
    PLAIN or d.ellipse([cx - 120, 30, cx + 120, 270], fill=(200, 160, 60))
    PLAIN or d.ellipse([cx - 100, 50, cx + 100, 250], fill=(245, 240, 225))
    PLAIN or d.ellipse([cx - 78, 72, cx + 78, 228], fill=(30, 60, 130))
    PLAIN or d.ellipse([cx - 40, 110, cx + 40, 190], fill=(200, 160, 60))
f = ImageFont.truetype(F + 'georgiab.ttf', 230)
t = "FOSTER'S"
bb = d.textbbox((0, 0), t, font=f)
x = (W - (bb[2] - bb[0])) // 2 - bb[0]; y = (H - (bb[3] - bb[1])) // 2 - bb[1]
PLAIN or d.text((x, y), t, font=f, fill=(255, 255, 255), stroke_width=9, stroke_fill=(25, 45, 110))
im.save(out + '/fosterssign.png')
# Carlton scoreboard face: deep blue, white script name, white rule under it
W, H = 1024, 512
im = Image.new('RGB', (W, H), (30, 90, 150)); d = ImageDraw.Draw(im)
d.rectangle([0, 0, W - 1, 18], fill=(240, 240, 240)); d.rectangle([0, H - 19, W - 1, H - 1], fill=(240, 240, 240))
f = ImageFont.truetype(F + 'segoescb.ttf', 220)
t = 'Carlton'
bb = d.textbbox((0, 0), t, font=f)
x = (W - (bb[2] - bb[0])) // 2 - bb[0]; y = (H - (bb[3] - bb[1])) // 2 - bb[1] - 30
PLAIN or d.text((x, y), t, font=f, fill=(255, 255, 255))
d.rectangle([180, 400, W - 180, 420], fill=(255, 255, 255))
im.save(out + '/carltonsign.png')
