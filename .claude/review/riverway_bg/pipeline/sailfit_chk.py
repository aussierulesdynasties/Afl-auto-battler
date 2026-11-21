import json, sys, numpy as np, canopies
from PIL import Image, ImageDraw
CP = np.array(json.load(open('data/riverway/prep/carports_cls.json')), float)
im = Image.open('data/riverway/sat.png').convert('RGB')
for g in (1, 2, 3):
    S = CP[CP[:, 4] == g]; P = S[:, :2]; x0, y0 = P.min(0) - 8; x1, y1 = P.max(0) + 8
    cr = im.crop((int((x0 + 1600) * 2), int((1600 - y1) * 2), int((x1 + 1600) * 2), int((1600 - y0) * 2))).resize((int((x1 - x0) * 4), int((y1 - y0) * 4)))
    d = ImageDraw.Draw(cr); n = 0
    for nm, V, F, C in canopies.build(S, lambda x, y: 0):
        if nm != 'bg_sails': continue
        for k in range(0, len(F), 36):
            n += 1; pts = [V[F[k][0]], V[F[k + 30][1]], V[F[k + 35][2]], V[F[k + 5][3]]]
            d.polygon([((p[0] - x0) * 4, (y1 - p[1]) * 4) for p in pts], outline=(255, 0, 0))
    print(g, n); cr.save(f'out/riverway/chk/sailfit_{g}.png')
