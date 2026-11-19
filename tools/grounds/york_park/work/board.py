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
# every texture's photo crop: ref/ photos (2016-2024), the 2024 new-seats photo (ws), the 2023 Centre West site photo (cw),
# and Google Earth 2026 views (ge/) where no photo shows the part. Boxes are (left, top, right, bottom) pixels.
SRC = {'d5': 'ref/UTAS-Stadium-drone5.jpg', 'a4': 'ref/utas-stadium-aerial4.jpg', 'gs': 'ref/UTAS-Stadium-grandstand.jpg',
       'ws': 'ref/utas-stadium-western-stand-new-seats.jpg', 'cw': 'ref/utas-stadium-centre-west-construction-site-fairbrother-1024x675.jpg',
       'l045': 'ge/l045.png', 'l225': 'ge/l225.png'}
REF = {'roof_white': ('d5', (430, 740, 640, 840)), 'facade_lattice': ('a4', (300, 460, 470, 525)), 'solar': ('a4', (500, 440, 700, 475)),
       'facade_nw': ('a4', (780, 455, 900, 530)), 'facade_es': ('d5', (1100, 690, 1180, 800)), 'facade_cw': ('gs', (650, 230, 800, 345)),
       'facade_pav': ('a4', (970, 355, 1050, 395)), 'screen_off': ('gs', (10, 335, 95, 370)),
       'seat_plastic': ('a4', (530, 315, 700, 338)), 'conc_tread': ('ws', (500, 290, 600, 338)), 'conc_wall': ('ws', (200, 185, 330, 215)),
       'fence': ('gs', (140, 416, 200, 432)), 'roof_soffit': ('ws', (280, 0, 560, 60)), 'fascia': ('d5', (760, 728, 900, 758)),
       'boxes_glass': ('ws', (380, 95, 580, 145)), 'glass': ('gs', (730, 265, 800, 300)), 'facade_gunns': ('l045', (640, 775, 1000, 840)),
       'facade_sw': ('cw', (200, 335, 300, 445)), 'roof_grey': ('l045', (540, 590, 640, 660)), 'board_frame': ('l045', (1015, 355, 1080, 405)),
       'board_back': ('l225', (805, 690, 860, 750)), 'board_side': ('gs', (70, 330, 108, 375)), 'panel_blue': ('a4', (1030, 400, 1075, 480)),
       'roof_flat': ('d5', (1110, 440, 1200, 500)), 'steel_galv': ('cw', (285, 215, 320, 360)), 'lamps': ('cw', (296, 205, 326, 255)),
       'paint_white': ('cw', (240, 368, 300, 396)), 'steel_maroon': ('cw', (205, 360, 240, 440)), 'paving': ('d5', (250, 610, 310, 680)),
       'steel_white': ('d5', (300, 760, 460, 880)), 'sign_utas': ('gs', (700, 205, 800, 265))}
tiles = sorted(glob.glob('model/tex/*.png')); S = 300
c = Image.new('RGB', (4 * (2 * S + 20), ((len(tiles) + 3) // 4) * (S + 40)), (30, 30, 30)); d = ImageDraw.Draw(c)
for i, f in enumerate(tiles):
    nm = os.path.basename(f)[:-4]; im = Image.open(f).convert('RGB'); sd = np.asarray(im.convert('L'), float).std()
    x, y = (i % 4) * (2 * S + 20), (i // 4) * (S + 40)
    w, h = im.size; k = min(w, h, 768); c.paste(im.crop((0, 0, k, k)).resize((S, S), Image.LANCZOS), (x, y + 36))
    if nm in REF:
        p, b = REF[nm]; pc = Image.open(SRC[p]).convert('RGB').crop(b); k2 = S / max(pc.size); pc = pc.resize((int(pc.width * k2), int(pc.height * k2)), Image.LANCZOS); c.paste(pc, (x + S + 4, y + 36))
    else:
        d.text((x + S + 14, y + 150), 'no photo crop\n(plain finish)', font=F, fill=(150, 150, 150))
    d.text((x + 4, y + 6), f'{nm}  grey sd {sd:.1f}   crop: ' + (('Google Earth 2026 ' if REF[nm][0].startswith('l') else 'photo ') + REF[nm][0]), font=F, fill=(255, 230, 0))
c.save(os.path.join(OUT, '5_textures_vs_photo.jpg'), quality=88); print('textures')

# 6 empty seats: from the boundary, and from seat height in an aisle, beside the empty-seat photo
def grid(items, name, W=960, H=540, cols=2):
    rows = (len(items) + cols - 1) // cols; c = Image.new('RGB', (cols * W, rows * H), (30, 30, 30))
    for i, (im, t) in enumerate(items):
        im = im.convert('RGB'); k = min(W / im.width, H / im.height); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        c.paste(label(im, t), ((i % cols) * W, (i // cols) * H))
    c.save(os.path.join(OUT, name), quality=90); print(name)


def crop(src, b): return Image.open(SRC.get(src, src)).convert('RGB').crop(b)


R_ = lambda n: Image.open(f'render/proofs/{n}.png')
grid([(R_('seatcu_north'), 'model: seat height, Northern stand aisle'), (R_('seatcu_gunns'), 'model: seat height, Gunns aisle'),
      (crop('ws', (0, 200, 600, 338)), 'photo: empty seats (2024)'), (crop('a4', (480, 300, 760, 350)), 'photo: seat colour, aerial')]
     + [(Image.open(f), 'model: ' + os.path.basename(f)[:-4]) for f in sorted(glob.glob('render/proofs/seats_*.png'))], '6_empty_seats.jpg')
# 8 scoreboards: each face beside the picture it was copied from
grid([(R_('board_ne_front'), 'model: NE board, front'), (crop('l045', (960, 300, 1130, 430)), 'Google Earth 2026 l045: NE board front, tower behind'),
      (R_('board_ne_back'), 'model: NE board, back'), (crop('l225', (770, 640, 900, 790)), 'Google Earth 2026 l225: NE board back'),
      (R_('board_sw_front'), 'model: SW board, front'), (crop('gs', (0, 90, 340, 450)), 'photo: SW board front (grandstand photo)'),
      (R_('board_sw_back'), 'model: SW board, back'), (crop('l045', (1020, 660, 1180, 830)), 'Google Earth 2026 l045: SW board back')], '8_scoreboards.jpg')
# 9 stand-back bracing: modelled steel beside the aerial
grid([(R_('facade_010_north_back'), 'model: Northern stand back'), (crop('a4', (260, 400, 760, 560)), 'photo: Northern stand back (aerial)'),
      (R_('facade_120_east_back'), 'model: East-South stand back'), (crop('d5', (900, 700, 1200, 860)), 'photo: East-South stand back (drone)')], '9_bracing.jpg')
# 10 crest: the painted crest beside the photo crop, both enlarged
t = Image.open('model/tex/sign_utas.png').convert('RGB'); tw, th = t.size
grid([(t.crop((0, 0, int(tw * 0.42), th)), 'texture: crest and lettering'), (crop('gs', (705, 215, 770, 262)), 'photo: crest and lettering (enlarged)'),
      (R_('sign_utas'), 'model: the sign from the pitch'), (crop('gs', (640, 180, 800, 300)), 'photo crop')], '10_crest_vs_photo.jpg')

# 7 sign: model render beside the photo crop, and the painted texture
r = Image.open('render/proofs/sign_utas.png').convert('RGB'); r.thumbnail((960, 540))
p = Image.open('ref/UTAS-Stadium-grandstand.jpg').convert('RGB').crop((640, 180, 800, 300)).resize((640, 480), Image.LANCZOS)
t = Image.open('model/tex/sign_utas.png').convert('RGB').resize((1600, 400), Image.LANCZOS)
c = Image.new('RGB', (1600, 540 + 400), (30, 30, 30)); c.paste(label(r, 'model, from the pitch'), (0, 0)); c.paste(label(p, 'photo crop'), (960, 30)); c.paste(t, (0, 540))
c.save(os.path.join(OUT, '7_sign_vs_photo.jpg'), quality=90); print('sign')
