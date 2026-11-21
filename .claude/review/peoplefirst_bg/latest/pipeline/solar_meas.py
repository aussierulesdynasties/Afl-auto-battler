import json, numpy as np
from PIL import Image, ImageDraw
A = np.asarray(Image.open('data/peoplefirst/sat.png').convert('RGB')).astype(int)
spec = json.load(open('spec/peoplefirst.json')); B = json.load(open('data/peoplefirst/prep/buildings.json'))
for sx, sy in spec['solar_roofs']:
    for b in B:
        P = np.array(b['p']); c = P.mean(0)
        if np.hypot(c[0] - sx, c[1] - sy) < 25:
            m = Image.new('L', (6000, 6000)); ImageDraw.Draw(m).polygon([((x + 1500) * 2, (1500 - y) * 2) for x, y in (c + (P - c) * .9)], fill=1); m = np.asarray(m, bool)
            px = A[m]; L = px.mean(1)
            print((sx, sy), 'roof px', m.sum(), 'panel frac (L<200)', round((L < 200).mean(), 3), 'panel median', np.median(px[L < 200], 0), 'roof median', np.median(px[L >= 200], 0))
