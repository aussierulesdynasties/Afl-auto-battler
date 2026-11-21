# Unwrap the Esri satellite around the origin: x = bearing (cw from north, 8 px/deg), y = radius (60..150 m, 4 px/m, outward down).
# Grid every 5 deg / 10 m. python work/polsat.py out_prefix
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = np.asarray(Image.open(os.path.join(SP, 'sat', 'esri_025.png')).convert('RGB'))
PX, PY, R0, R1 = 8, 4, 50, 150
for b0 in range(0, 360, 90):
    bs = b0 + np.arange(90 * PX) / PX; rs = R0 + np.arange((R1 - R0) * PY) / PY
    B, R = np.meshgrid(np.radians(bs), rs)
    u = np.clip(((R * np.sin(B) + 260) * 4).astype(int), 0, 2079); v = np.clip(((260 - R * np.cos(B)) * 4).astype(int), 0, 2079)
    im = Image.fromarray(S[v, u]).resize((90 * PX * 2, (R1 - R0) * PY * 2), Image.LANCZOS); d = ImageDraw.Draw(im)
    for b in range(b0, b0 + 91, 5):
        x = (b - b0) * PX * 2; d.line([(x, 0), (x, im.height)], fill=(255, 0, 255), width=1); d.text((x + 2, 2), str(b % 360), fill=(255, 0, 255))
    for r in range(R0, R1 + 1, 10):
        y = (r - R0) * PY * 2; d.line([(0, y), (im.width, y)], fill=(0, 255, 255), width=1); d.text((2, y + 1), str(r), fill=(0, 255, 255))
    im.save(f'{sys.argv[1]}_{b0:03d}.png')
print('ok')
