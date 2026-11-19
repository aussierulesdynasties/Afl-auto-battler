# East roof edge proof board: (1) g49 with model edges, arrows from where the camera fit puts three satellite-placed
# objects to where the photo shows them; (2) top-down at y = 0 m, satellite above model, 5 m ticks.
import numpy as np, json
from PIL import Image, ImageDraw
exec(open('cam.py').read())
P = np.array(json.load(open('camfit10.json'))['p'])
NE = [('fan drum, big', (116.0, 62.9, 19.3), (335.5, 888.5)), ('fan drum, small', (119.2, 56.3, 19.3), (321, 875)),
      ('Gate 7 corner', (111.5, 81.5, 8.5), (380, 971))]
ed = Image.open('v6_edges.png').convert('RGB'); box = (200, 560, 560, 1040); S = 2
a = ed.crop(box).resize(((box[2] - box[0]) * S, (box[3] - box[1]) * S), Image.LANCZOS); d = ImageDraw.Draw(a)
T = lambda q: ((q[0] - box[0]) * S, (q[1] - box[1]) * S)
for n, X, u in NE:
    m = proj(P, [X])[0]; L = float(np.hypot(*(np.array(u) - m)))
    d.line([T(m), T(u)], fill=(255, 255, 0), width=3); d.ellipse([T(u)[0] - 5, T(u)[1] - 5, T(u)[0] + 5, T(u)[1] + 5], outline=(0, 255, 0), width=3)
    d.ellipse([T(m)[0] - 5, T(m)[1] - 5, T(m)[0] + 5, T(m)[1] + 5], outline=(255, 255, 0), width=3)
    d.text((T(m)[0] + 8, T(m)[1] + 4), '%s: %d px' % (n, round(L)), fill=(255, 255, 0))
d.rectangle([0, 0, a.size[0], 40], fill=(0, 0, 0))
d.text((8, 6), 'g49 + model edges (magenta). Yellow = where the camera puts a satellite-placed object, green = the photo.', fill=(255, 255, 255))
d.text((8, 22), 'Same offset, same direction as the east roof edge: the camera fit, not the model.', fill=(255, 255, 255))
s = Image.open('sat/sat_model11135.png').convert('RGB'); t = Image.open('top_l.png').convert('RGBA')
bg = Image.new('RGBA', t.size, (0, 0, 0, 255)); bg.alpha_composite(t); t = bg.convert('RGB')
py = 800; bx = (800 + 4 * 95, py - 50, 800 + 4 * 125, py + 50)
cols = []
for lab, im in (('satellite (2011 tile, lean-matched)', s), ('model top-down, same lean', t)):
    c = im.crop(bx).resize((480, 400), Image.LANCZOS); dd = ImageDraw.Draw(c)
    for xm in range(95, 126, 5):
        X = (800 + 4 * xm - bx[0]) * 4; dd.line([(X, 30), (X, 400)], fill=(255, 255, 0)); dd.text((X + 2, 32), '%d m' % xm, fill=(255, 255, 0))
    dd.rectangle([0, 0, 480, 26], fill=(0, 0, 0)); dd.text((6, 6), lab + ', east side at y = 0', fill=(255, 255, 255)); cols.append(c)
b = Image.new('RGB', (a.size[0] + 500, max(a.size[1], 820)), (20, 20, 20))
b.paste(a, (0, 0)); b.paste(cols[0], (a.size[0] + 10, 0)); b.paste(cols[1], (a.size[0] + 10, 410))
b.save('east_edge_proof.png'); print(b.size)
