# Texture board per surface type: photo crop (ge/<view>) | render crop at game distance (rr/<view>, same box) |
# the hand-painted tile itself (3 m square at full resolution, with its stddev) | a close render where one exists.
# The view and box per surface come from the ID renders (rf/id16: material colour = md5 of its name, work/idname.py):
# the view where the surface shows most, a 360x240 box around its densest patch.
# python work/surfboard.py <out.png> [close_dir]  (close_dir holds the close renders; sg_mcc.png and sg_warne.png are
# copies of the two sign close views from sg/)
import sys, os, json, glob, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from idname import table
from PIL import Image, ImageDraw
out = sys.argv[1]; cdir = sys.argv[2] if len(sys.argv) > 2 else None
SURF = ['seat_navy', 'seat_grey', 'seat_moss', 'aisle_light', 'tier_fascia', 'fascia_mcc', 'tier_wall', 'roof_white', 'roof_grey',
        'roof_teal', 'roof_soffit', 'steel_blue', 'steel_white', 'conc_light', 'paving', 'fence', 'grass']
CLOSE = {'seat_navy': 'sg_warne', 'tier_fascia': 'sg_warne', 'seat_moss': 'sg_mcc', 'fascia_mcc': 'sg_mcc', 'roof_soffit': 'sg_mcc',
         'steel_blue': 'join_100_roof_facade_east', 'roof_white': 'join_100_roof_facade_east', 'paving': 'facade_242_sw_pale',
         'steel_white': 'join_300_truss_feet_west', 'aisle_light': 'sg_warne'}
TILE = json.load(open('model/tex/tiles.json')); T = table(SURF); BW, BH = 360, 240
ids = {os.path.basename(f)[:-4]: np.asarray(Image.open(f).convert('RGBA')).astype(float) for f in sorted(glob.glob('rf/id16/*.png'))}
rows = []
for n in SURF:
    best = None
    for v, r in ids.items():
        if not os.path.exists('ge/%s.png' % v) or not os.path.exists('rr/%s.png' % v): continue
        m = (np.abs(r[:, :, :3] - T[n]).sum(2) < 5) & (r[:, :, 3] > 250)
        if m.sum() < 400: continue
        ys, xs = np.nonzero(m)  # densest patch: the box (at a coarse grid) holding the most of the surface
        H_, W_ = m.shape; ii = np.cumsum(np.cumsum(m, 0), 1)
        def cnt(x, y): x1, y1 = min(W_ - 1, x + BW), min(H_ - 1, y + BH); return ii[y1, x1] - ii[y, x1] - ii[y1, x] + ii[y, x]
        c, x, y = max((cnt(x, y), x, y) for y in range(0, H_ - BH, 40) for x in range(0, W_ - BW, 40))
        if best is None or c > best[0]: best = (c, v, (x, y, x + BW, y + BH))
    if best is None: print('not seen', n); continue
    c, v, box = best
    ph = Image.open('ge/%s.png' % v).convert('RGB').crop(box)
    r = Image.open('rr/%s.png' % v).convert('RGBA'); bg = Image.new('RGBA', r.size, (0, 0, 0, 255)); bg.alpha_composite(r)
    rc = bg.convert('RGB').crop(box)
    a = Image.open('model/tex/%s.png' % n).convert('RGB'); tw, tv = TILE[n]; px = a.size[0] / tw
    sw = a.crop((0, 0, int(min(a.size[0], 3 * px)), int(min(a.size[1], 3 * a.size[1] / tv)))).resize((BH, BH))
    sd = np.asarray(a, float).mean(2).std()
    cl = Image.new('RGB', (BW, BH), (40, 40, 40))
    if cdir and n in CLOSE:
        p = os.path.join(cdir, CLOSE[n] + '.png')
        if os.path.exists(p):
            im = Image.open(p).convert('RGB'); w, h = im.size; cl = im.crop((w // 4, h // 4, w * 3 // 4, h * 3 // 4)).resize((BW, BH))
    row = Image.new('RGB', (BW * 3 + BH + 24, BH + 20), (20, 20, 20)); d = ImageDraw.Draw(row)
    for k, im in enumerate((ph, rc)): row.paste(im, (k * (BW + 8), 20))
    row.paste(sw, (2 * (BW + 8), 20)); row.paste(cl, (2 * (BW + 8) + BH + 8, 20))
    d.text((4, 4), '%s   photo %s | render %s (game distance) | hand-painted tile 3 m, stddev %.1f | close render%s'
           % (n, v, v, sd, ' (' + CLOSE[n] + ')' if n in CLOSE else ' (none)'), fill=(255, 255, 0))
    rows.append(row); print(n, v, box, round(sd, 1))
B = Image.new('RGB', (rows[0].size[0], sum(r.size[1] + 4 for r in rows)), (0, 0, 0)); y = 0
for r in rows: B.paste(r, (0, y)); y += r.size[1] + 4
B.save(out); print(B.size)
