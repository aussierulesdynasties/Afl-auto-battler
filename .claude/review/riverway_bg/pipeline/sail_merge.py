# Merge hand-traced field 1 sections (sail_trace.json) with hand-placed fields 2/3 into sails.json; draw the whole field 1 overlay.
import json, subprocess, sys
from PIL import Image, ImageDraw
T = json.load(open('data/riverway/prep/sail_trace.json'))
subprocess.run([sys.executable, '-E', 'sail_manual.py'], check=True)
S = [s for s in json.load(open('data/riverway/prep/sails.json')) if s['g'] != 1]
for n, s in T['sections'].items():
    for q in s['sails']: S.append({'g': 1, 'sec': n, 'corners': [[s['x0'] + p[0] / 16, s['y1'] - p[1] / 16] for p in q]})
json.dump(S, open('data/riverway/prep/sails.json', 'w'))
x0, x1, y0, y1 = -620, -400, 40, 175; Z = 4
im = Image.open('data/riverway/sat.png').convert('RGB').crop((int((x0+1600)*2), int((1600-y1)*2), int((x1+1600)*2), int((1600-y0)*2)))
im = im.resize((im.width*Z, im.height*Z), Image.LANCZOS); d = ImageDraw.Draw(im)
for s in S:
    if s['g'] != 1: continue
    P = [((x-x0)*2*Z, (y1-y)*2*Z) for x, y in s['corners']]; d.polygon(P, outline=(255, 0, 0)); d.polygon([(a+1, b+1) for a, b in P], outline=(255, 0, 0))
im.save('out/riverway/chk/sails_traced_1.png')
from collections import Counter; print(Counter(s['g'] for s in S))
