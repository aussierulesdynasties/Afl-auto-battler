"""photo | render side board (type look comparison, not camera-matched). python py/side.py photo render out label"""
import sys
from PIL import Image, ImageDraw
a = Image.open(sys.argv[1]).convert("RGB"); b = Image.open(sys.argv[2]).convert("RGB"); H = 700
a = a.resize((int(a.width * H / a.height), H)); b = b.resize((int(b.width * H / b.height), H))
W = Image.new("RGB", (a.width + b.width + 10, H + 34), (20, 20, 22)); W.paste(a, (0, 34)); W.paste(b, (a.width + 10, 34))
d = ImageDraw.Draw(W); d.text((8, 10), "reference photo", fill=(255, 255, 255)); d.text((a.width + 18, 10), sys.argv[4], fill=(255, 255, 255))
W.save(sys.argv[3], quality=88)
