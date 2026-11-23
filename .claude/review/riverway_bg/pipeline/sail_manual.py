# Hand-digitised sails (centre x, y in scene metres) per field, with field angle and sail size, from sailgrid_*.png
import json, numpy as np
from PIL import Image, ImageDraw
F = json.load(open('data/riverway/prep/sails_manual.json'))
CP = np.array(json.load(open('data/riverway/prep/carports_cls.json')), float)
im = Image.open('data/riverway/sat.png').convert('RGB'); out = []
for f in F:
    g = f['g']; S = CP[CP[:, 4] == g][:, :2]; x0, y0 = np.floor(S.min(0) / 10) * 10 - 10; x1, y1 = np.ceil(S.max(0) / 10) * 10 + 10
    v = im.crop((int((x0 + 1600) * 2), int((1600 - y1) * 2), int((x1 + 1600) * 2), int((1600 - y0) * 2)))
    Z = 6; v = v.resize((v.width * Z, v.height * Z), Image.LANCZOS); d = ImageDraw.Draw(v)
    th = np.radians(f['angle']); a = np.array([np.cos(th), np.sin(th)]); b = np.array([-a[1], a[0]])
    for i, s in enumerate(f['sails']):
        c = np.array(s[:2]); w, h = (s[2], s[3]) if len(s) > 2 else (f['w'], f['h'])
        cn = [c + a * su * w / 2 + b * sv * h / 2 for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        out.append({'g': g, 'corners': [list(map(float, q)) for q in cn]})
        P = [((q[0] - x0) * 2 * Z, (y1 - q[1]) * 2 * Z) for q in cn]
        d.polygon(P, outline=(255, 0, 0)); d.polygon([(p[0] + 1, p[1] + 1) for p in P], outline=(255, 0, 0))
        d.text(((c[0] - x0) * 2 * Z, (y1 - c[1]) * 2 * Z), str(i), fill=(255, 255, 0))
    v.save(f'out/riverway/chk/sailman_{g}.png'); print(g, len(f['sails']))
json.dump(out, open('data/riverway/prep/sails.json', 'w'))
