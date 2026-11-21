# python work/board.py out_dir : the READY-FOR-GATE boards for Riverway Stadium (overlays, turntable sheet, facades and
# joins, top-down, textures vs photo crops, empty seats, sign). Run from tools/grounds/riverway after the proofs job.
import sys, os, glob, numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageFont
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
        c.paste(label(o.resize((W, H), Image.LANCZOS), f'model {v}: 55% over GE, magenta outline, cyan edges'), (W, i * H))
    c.save(os.path.join(OUT, name), quality=88); print(name)


def grid(items, name, W=960, H=540, cols=2):
    rows = (len(items) + cols - 1) // cols; c = Image.new('RGB', (cols * W, rows * H), (30, 30, 30))
    for i, (im, t) in enumerate(items):
        im = im.convert('RGB'); k = min(W / im.width, H / im.height); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        c.paste(label(im, t), ((i % cols) * W, (i // cols) * H))
    c.save(os.path.join(OUT, name), quality=90); print(name)


SRC = {'sg': 'ref/symonds-grandstand-riverway.jpg', 'au': 'ref/ausleisure.jpg', 'rs': 'ref/riverway-stadium.jpg',
       'l090': 'ge/l090.png', 'c270': 'ge/c270.png'}
R_ = lambda n: Image.open(f'render/proofs/{n}.png')
def crop(src, b): return Image.open(SRC.get(src, src)).convert('RGB').crop(b)


# 1 overlays: every Google Earth view with the model laid over it
pairs(['l000', 'l045', 'l090', 'l135'], '1a_overlays_l000-l135.jpg')
pairs(['l180', 'l225', 'l270', 'l315'], '1b_overlays_l180-l315.jpg')
pairs(['c000', 'c090', 'c180', 'c270'], '1c_overlays_close.jpg')

# 2 turntable stills (the film is 2_turntable.mp4)
grid([(R_(f'turntable_{a:03d}'), f'turntable {a} deg') for a in range(0, 360, 45)], '2_turntable_stills.jpg')

# 3 facades and joins at full proof resolution, two per row
grid([(Image.open(f), os.path.basename(f)[:-4]) for f in sorted(glob.glob('render/proofs/facade_*.png'))], '3a_facades.jpg')
grid([(Image.open(f), os.path.basename(f)[:-4]) for f in sorted(glob.glob('render/proofs/join_*.png'))]
     + [(R_('screen_front'), 'screen_front'), (R_('screen_back'), 'screen_back')], '3b_joins_screen.jpg')

# 4 top-down over the satellite (4 px/m, 10 m grid): whole ground, then the stand at 2x
T = Image.open('render/topov.png').convert('RGB')
T.resize((1560, 1560), Image.LANCZOS).save(os.path.join(OUT, '4a_topdown_vs_satellite.jpg'), quality=90)
label(T.crop((300, 500, 1000, 1500)).resize((1400, 2000), Image.LANCZOS), 'stand, sails, race and shelters at 2x; grid 10 m').save(
    os.path.join(OUT, '4b_topdown_stand.jpg'), quality=90)

# 5 textures: hand-made tile beside the photo or Google Earth crop it copies, grey sd printed
REF = {'seat_green': ('sg', (0, 95, 300, 200)), 'seat_teal': ('sg', (560, 150, 900, 230)), 'seat_blue': ('sg', (0, 95, 300, 200)),
       'seat_plastic': ('sg', (900, 190, 1200, 280)), 'conc_tread': ('sg', (500, 160, 620, 240)),
       'podium': ('sg', (930, 300, 1200, 345)), 'glass_corp': ('sg', (0, 0, 580, 95)), 'roof_soffit': ('sg', (600, 0, 1200, 130)),
       'sign_symonds': ('sg', (100, 180, 515, 248)), 'sign_home': ('sg', (205, 232, 355, 262)), 'sign_away': ('sg', (405, 245, 535, 275)),
       'race_gates': ('sg', (170, 270, 470, 420)), 'steel_galv': ('sg', (320, 280, 350, 430)),
       'shelter_wall': ('au', (175, 560, 320, 600)), 'shelter_roof': ('au', (545, 500, 675, 530)), 'lamps': ('rs', (80, 105, 152, 128)),
       'facade_back': ('l090', (800, 770, 1120, 840)), 'roof_grey': ('l090', (740, 690, 840, 760)), 'solar': ('l090', (800, 700, 1040, 750)),
       'sail_blue': ('l090', (650, 705, 745, 755)), 'screen_off': ('l090', (608, 336, 684, 392)), 'fascia': ('sg', (580, 100, 1200, 150))}
tiles = sorted(glob.glob('model/tex/*.png')); S = 300; std = []
c = Image.new('RGB', (4 * (2 * S + 20), ((len(tiles) + 3) // 4) * (S + 40)), (30, 30, 30)); d = ImageDraw.Draw(c)
for i, f in enumerate(tiles):
    nm = os.path.basename(f)[:-4]; im = Image.open(f).convert('RGB'); sd = np.asarray(im.convert('L'), float).std(); std.append((nm, sd))
    x, y = (i % 4) * (2 * S + 20), (i // 4) * (S + 40)
    w, h = im.size; k = min(w, h, 768); c.paste(im.crop((0, 0, k, k)).resize((S, S), Image.LANCZOS), (x, y + 36))
    src = ''
    if nm in REF:
        p, b = REF[nm]; pc = crop(p, b); k2 = S / max(pc.size); pc = pc.resize((max(1, int(pc.width * k2)), max(1, int(pc.height * k2))), Image.LANCZOS)
        c.paste(pc, (x + S + 4, y + 36)); src = ('Google Earth ' if p.startswith(('l', 'c')) else 'photo ') + p
    else:
        d.text((x + S + 14, y + 150), 'no photo crop\n(plain finish)', font=F, fill=(150, 150, 150))
    d.text((x + 4, y + 6), f'{nm}  grey sd {sd:.1f}  {src}', font=F, fill=(255, 230, 0))
c.save(os.path.join(OUT, '5_textures_vs_photo.jpg'), quality=88)
open(os.path.join(OUT, '5_texture_stddev.txt'), 'w').write(''.join(f'{n:16s} grey sd {s:5.1f}\n' for n, s in std)); print('textures')

# 6 empty seats: seat height and boundary views beside the photo
grid([(R_('seatcu_centre'), 'model: seat height, centre aisle'), (crop('sg', (0, 80, 600, 210)), 'photo: empty seats'),
      (R_('seatcu_south'), 'model: seat height, south'), (R_('seatcu_under_front'), 'model: front rows from below')]
     + [(Image.open(f), 'model: ' + os.path.basename(f)[:-4]) for f in sorted(glob.glob('render/proofs/seats_*.png'))], '6_empty_seats.jpg')

# 7 sign: model beside the photo crop, and the painted texture
grid([(R_('sign_symonds'), 'model: race, sign and HOME/AWAY boards'), (crop('sg', (90, 170, 560, 430)), 'photo crop'),
      (ImageOps.expand(Image.open('model/tex/sign_symonds.png').convert('RGB'), border=(0, 120, 0, 0), fill=(30, 30, 30)), 'texture: sign_symonds (hand-made, Barlow SemiBold)'), (crop('sg', (100, 180, 515, 248)), 'photo: the sign')],
     '7_sign_vs_photo.jpg')
