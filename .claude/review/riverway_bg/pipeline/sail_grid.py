import json, numpy as np
from PIL import Image, ImageDraw
CP = np.array(json.load(open('data/riverway/prep/carports_cls.json')), float)
im = Image.open('data/riverway/sat.png').convert('RGB')
for g in (1, 2, 3):
    S = CP[CP[:, 4] == g][:, :2]; x0, y0 = np.floor(S.min(0) / 10) * 10 - 10; x1, y1 = np.ceil(S.max(0) / 10) * 10 + 10
    v = im.crop((int((x0 + 1600) * 2), int((1600 - y1) * 2), int((x1 + 1600) * 2), int((1600 - y0) * 2)))
    Z = 6; v = v.resize((v.width * Z, v.height * Z), Image.LANCZOS); d = ImageDraw.Draw(v)
    for x in np.arange(x0, x1 + 1, 10):
        X = (x - x0) * 2 * Z; d.line([(X, 0), (X, v.height)], fill=(0, 255, 255) if x % 50 else (255, 255, 0))
        d.text((X + 2, 2), str(int(x)), fill=(255, 255, 0))
    for y in np.arange(y0, y1 + 1, 10):
        Y = (y1 - y) * 2 * Z; d.line([(0, Y), (v.width, Y)], fill=(0, 255, 255) if y % 50 else (255, 255, 0))
        d.text((2, Y + 2), str(int(y)), fill=(255, 255, 0))
    v.save(f'out/riverway/chk/sailgrid_{g}.png'); print(g, x0, x1, y0, y1, v.size)
