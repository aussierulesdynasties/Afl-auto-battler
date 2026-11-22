import json, numpy as np; from PIL import Image
b = json.load(open('data/optus/prep/forecourt.json')); fc = Image.open('data/optus/prep/forecourt.png')
x0, x1, y0, y1 = 90, 250, -135, -15
c = fc.crop((int((x0 - b['x0']) / .1), int((b['y1'] - y1) / .1), int((x1 - b['x0']) / .1), int((b['y1'] - y0) / .1))).resize((1280, 960))
bg = Image.new('RGBA', c.size, (200, 120, 110, 255)); bg.alpha_composite(c)
a = Image.open('data/optus/sat_hi_south.png').convert('RGB')
s = Image.new('RGB', (1280, 1920)); s.paste(a, (0, 0)); s.paste(bg.convert('RGB'), (0, 960)); s.resize((800, 1200)).save('_south_cmp.jpg', quality=88)
