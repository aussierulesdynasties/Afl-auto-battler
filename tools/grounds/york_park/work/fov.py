# Overlay the fence ellipse (z=0) and a 10 m-high ring at the fence on a GE view: python work/fov.py l000 out.png
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gecam as G
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = json.load(open(os.path.join(SP, 'work', 'fence.json')))['er']
v, out = sys.argv[1], sys.argv[2]
im = Image.open(os.path.join(SP, 'ge', v + '.png')).convert('RGB'); d = ImageDraw.Draw(im)
pts = [(r * math.sin(math.radians(b)), r * math.cos(math.radians(b))) for b, r in F]
for z, col in ((0, (255, 0, 255)),):
    q = G.P(v, [[x, y, z] for x, y in pts]); d.line([tuple(p) for p in q] + [tuple(q[0])], fill=col, width=2)
q = G.P(v, [[0, 0, 0]]); d.ellipse([q[0][0] - 5, q[0][1] - 5, q[0][0] + 5, q[0][1] + 5], outline=(255, 255, 0), width=2)
im.save(out); print(out)
