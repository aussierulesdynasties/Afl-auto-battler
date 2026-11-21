import json, sys; from PIL import Image, ImageDraw
H = json.load(open('spec/optus_fc_hand.json')); im = Image.open('data/optus/sat_hi_south.png').convert('RGB'); d = ImageDraw.Draw(im)
C = {'bed': (255, 0, 255), 'mulch_gold': (255, 255, 0), 'lawn': (0, 255, 0), 'concrete': (0, 255, 255), 'asphalt': (255, 128, 0), 'stair': (255, 255, 255)}
for i, p in enumerate(H['south']):
    q = [((x - 90) / .125, (-15 - y) / .125) for x, y in p['pts']]; d.line(q + [q[0]], fill=C[p['kind']], width=2); d.text(q[0], str(i), fill=C[p['kind']])
q = [((x - 90) / .125, (-15 - y) / .125) for x, y in H['south_hut']]; d.line(q + [q[0]], fill=(255, 0, 0), width=2)
for x in range(90, 251, 10): d.text(((x - 90) / .125 + 2, 2), str(x), fill=(255, 255, 255))
for y in range(-20, -136, -10): d.text((2, (-15 - y) / .125), str(y), fill=(255, 255, 255))
im.save('_sov.jpg', quality=90)
