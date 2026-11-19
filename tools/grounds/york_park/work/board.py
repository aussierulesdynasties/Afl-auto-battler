# python work/board.py out_dir : the READY-FOR-GATE boards (overlays, top-down, textures vs photo crops, seats, sign)
import sys, os, glob, json, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)


def label(im, t):
    d = ImageDraw.Draw(im); d.rectangle((0, 0, 12 * len(t) + 16, 30), fill=(20, 20, 20)); d.text((6, 3), t, font=F, fill=(255, 230, 0)); return im


def overlay(v):
    g = Image.open(f'ge/{v}.png').convert('RGB'); r = Image.open(f'render/{v}.png').convert('RGBA')
    A = np.asarray(r, float); o = np.asarray(g, float).copy(); m = A[:, :, 3] / 255
    e = np.asarray(Image.fromarray((m > 0.5).astype(np.uint8) * 255).filter(ImageFilter.FIND_EDGES)) > 0
    L = np.asarray(Image.fromarray((A[:, :, :3] @ [0.3, 0.59, 0.11]).astype(np.uint8)).filter(ImageFilter.FIND_EDGES))
    mm = (m * 0.55)[:, :, None]; o = o * (1 - mm) + A[:, :, :3] * mm; e2 = (L > 90) & (m > 0.5); o[e2] = (0, 255, 255); o[e] = (255, 0, 255)
    return g, Image.fromarray(o.clip(0, 255).astype(np.uint8))


def pairs(views, name):
    W, H = 960, 540; c = Image.new('RGB', (2 * W, len(views) * H))
    for i, v in enumerate(views):
        g, o = overlay(v)
        c.paste(label(g.resize((W, H), Image.LANCZOS), f'Google Earth {v}'), (0, i * H))
        c.paste(label(o.resize((W, H), Image.LANCZOS), f'model {v}: 55% model over GE, magenta outline, cyan edges'), (W, i * H))
    c.save(os.path.join(OUT, name), quality=88); print(name)


pairs(['l000', 'l045', 'l090', 'l135'], '1a_overlays_l000-l135.jpg')
pairs(['l180', 'l225', 'l270', 'l315'], '1b_overlays_l180-l315.jpg')
pairs(['o000', 'o090', 'o180', 'o270'], '1c_overlays_far.jpg')

# 4 top-down: re-leaned model over the satellite, whole and by quadrant (10 m grid)
T = Image.open('render/topov_relean.png').convert('RGB')
T.resize((1560, 1560), Image.LANCZOS).save(os.path.join(OUT, '4a_topdown_vs_satellite.jpg'), quality=90)
q = Image.new('RGB', (2080, 2080))
for i, (x, y) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
    q.paste(T.crop((200 + x * 840, 200 + y * 840, 1040 + x * 840, 1040 + y * 840)).resize((1040, 1040), Image.LANCZOS), (x * 1040, y * 1040))
label(q, 'quadrants NW NE / SW SE at 2x; grid 10 m; cyan model outline, magenta model edges').save(os.path.join(OUT, '4b_topdown_quadrants.jpg'), quality=90)

# 5 textures: hand-made tile beside the photo crop it copies, grey sd printed
REF = {'roof_white': ('UTAS-Stadium-drone5.jpg', (430, 740, 640, 840)),
       'facade_lattice': ('utas-stadium-aerial4.jpg', (300, 460, 470, 525)),
       'solar': ('utas-stadium-aerial4.jpg', (500, 440, 700, 475)),
       'facade_nw': ('utas-stadium-aerial4.jpg', (780, 455, 900, 530)),
       'facade_es': ('UTAS-Stadium-drone5.jpg', (1100, 690, 1180, 800)),
       'facade_cw': ('UTAS-Stadium-grandstand.jpg', (650, 230, 800, 345)),
       'seats_green': ('utas-stadium-aerial4.jpg', (530, 315, 700, 340)),
       'facade_pav': ('utas-stadium-aerial4.jpg', (970, 355, 1050, 395)),
       'screen_off': ('UTAS-Stadium-grandstand.jpg', (10, 335, 95, 370))}
tiles = sorted(glob.glob('model/tex/*.png')); S = 300
c = Image.new('RGB', (4 * (2 * S + 20), ((len(tiles) + 3) // 4) * (S + 40)), (30, 30, 30)); d = ImageDraw.Draw(c)
for i, f in enumerate(tiles):
    nm = os.path.basename(f)[:-4]; im = Image.open(f).convert('RGB'); sd = np.asarray(im.convert('L'), float).std()
    x, y = (i % 4) * (2 * S + 20), (i // 4) * (S + 40)
    w, h = im.size; k = min(w, h, 768); c.paste(im.crop((0, 0, k, k)).resize((S, S), Image.LANCZOS), (x, y + 36))
    if nm in REF:
        p, b = REF[nm]; pc = Image.open('ref/' + p).convert('RGB').crop(b); k2 = S / max(pc.size); pc = pc.resize((int(pc.width * k2), int(pc.height * k2)), Image.LANCZOS); c.paste(pc, (x + S + 4, y + 36))
    else:
        d.text((x + S + 14, y + 150), 'no photo crop\n(plain finish)', font=F, fill=(150, 150, 150))
    d.text((x + 4, y + 6), f'{nm}  grey sd {sd:.1f}', font=F, fill=(255, 230, 0))
c.save(os.path.join(OUT, '5_textures_vs_photo.jpg'), quality=88); print('textures')

# 6 empty seats
ims = [Image.open(f).convert('RGB').resize((960, 540), Image.LANCZOS) for f in sorted(glob.glob('render/proofs/seats_*.png'))]
c = Image.new('RGB', (960, 540 * len(ims)))
for i, im in enumerate(ims): c.paste(im, (0, i * 540))
c.save(os.path.join(OUT, '6_empty_seats.jpg'), quality=90)

# 7 sign: model render beside the photo crop, and the painted texture
r = Image.open('render/proofs/sign_utas.png').convert('RGB'); r.thumbnail((960, 540))
p = Image.open('ref/UTAS-Stadium-grandstand.jpg').convert('RGB').crop((640, 180, 800, 300)).resize((640, 480), Image.LANCZOS)
t = Image.open('model/tex/sign_utas.png').convert('RGB').resize((1600, 400), Image.LANCZOS)
c = Image.new('RGB', (1600, 540 + 400), (30, 30, 30)); c.paste(label(r, 'model, from the pitch'), (0, 0)); c.paste(label(p, 'photo crop'), (960, 30)); c.paste(t, (0, 540))
c.save(os.path.join(OUT, '7_sign_vs_photo.jpg'), quality=90); print('sign')
