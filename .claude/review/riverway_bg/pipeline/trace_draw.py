# Hand-traced sail corners per section (px on tr_<n>.png, 16 px/m) -> scene metres; draws overlay tr_<n>_ov.png.
import json, sys
from PIL import Image, ImageDraw
T = json.load(open('data/riverway/prep/sail_trace.json'))
for n, s in T['sections'].items():
    x0, y1 = s['x0'], s['y1']; im = Image.open(f'out/riverway/chk/tr_{n}.png'); d = ImageDraw.Draw(im)
    for i, q in enumerate(s['sails']):
        d.polygon([tuple(p) for p in q], outline=(255, 0, 0)); d.polygon([(p[0]+1, p[1]+1) for p in q], outline=(255, 0, 0))
        d.text((sum(p[0] for p in q)/4, sum(p[1] for p in q)/4), f'{n}{i}', fill=(255, 255, 0))
    im.save(f'out/riverway/chk/tr_{n}_ov.png')
