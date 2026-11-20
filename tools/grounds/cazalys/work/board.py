# Proof board panels for the gate: one PNG per panel, labelled, into .claude/review/cazalys/
import os, glob, sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
G = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = os.path.join(G, '..', '..', '..', '.claude', 'review', 'cazalys')
os.makedirs(R, exist_ok=True); F = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 26)
def lab(im, t):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, d.textlength(t, font=F) + 16, 38], fill=(0, 0, 0)); d.text((8, 5), t, font=F, fill=(255, 255, 255)); return im
def grid(items, cols, w, name):
    ims = []
    for f, t in items:
        im = Image.open(f).convert('RGB'); im = im.resize((w, int(im.height * w / im.width))); ims.append(lab(im, t))
    h = max(i.height for i in ims); rows = (len(ims) + cols - 1) // cols
    S = Image.new('RGB', (cols * w, rows * h), (20, 20, 20))
    for k, im in enumerate(ims): S.paste(im, ((k % cols) * w, (k // cols) * h))
    S.save(os.path.join(R, name)); print(name, S.size)
p = lambda *a: os.path.join(G, *a)
grid([(p('render', f'ov_{v}.jpg'), f'GE {v} vs model overlay') for v in ('n020', 'n110', 'n200', 'n290', 'l000', 'l180')], 2, 1200, 'board_1_overlays.png')
grid([(p('render', 'topov.png'), 'top-down: model outline on aerial (within ~2 m)')], 1, 1800, 'board_2_top.png')
grid([(f, 'turntable ' + os.path.basename(f)[10:13]) for f in sorted(glob.glob(p('out', 'turntable_*.png')))], 2, 1200, 'board_3_turntable.png')
grid([(f, os.path.basename(f)[:-4]) for f in sorted(glob.glob(p('out', 'facade_*.png')))], 2, 1200, 'board_4_facades.png')
grid([(f, os.path.basename(f)[:-4]) for f in sorted(glob.glob(p('out', 'join_*.png')))], 2, 1200, 'board_5_joins.png')
grid([(f, os.path.basename(f)[:-4]) for f in sorted(glob.glob(p('out', 'seat*.png')))], 2, 1200, 'board_6_seats.png')
grid([(p('out', 'sign_gate.png'), 'model: gate'), (p('render', 'p_01.jpg'), 'photo 01 crop: gate'),
      (p('out', 'sign_scoreboard.png'), 'model: scoreboard'), (p('render', 'p_07.jpg'), 'photo 07 crop: scoreboard'),
      (p('out', 'sign_scoreboard_top.png'), 'model: scoreboard top'), (p('render', 'p_07.jpg'), 'photo 07 crop: scoreboard script'),
      (p('out', 'sign_hopgood.png'), 'model: Hopgood sign'), (p('render', 'p_02.jpg'), 'photo 02 crop: Hopgood')], 2, 1200, 'board_7_signs.png')
# textures with grey stddev (flat-fill check)
ts = sorted(glob.glob(p('model', 'tex', '*.png'))); cell = 300; cols = 6; rows = (len(ts) + cols - 1) // cols
S = Image.new('RGB', (cols * cell, rows * (cell + 40)), (20, 20, 20)); d = ImageDraw.Draw(S); f2 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 20)
for k, f in enumerate(ts):
    im = Image.open(f).convert('RGB'); sd = np.asarray(im.convert('L'), float).std()
    x, y = (k % cols) * cell, (k // cols) * (cell + 40); S.paste(im.resize((cell - 6, cell - 6)), (x + 3, y + 40))
    d.text((x + 4, y + 8), f'{os.path.basename(f)[:-4]}  sd {sd:.1f}', font=f2, fill=(255, 255, 255))
S.save(os.path.join(R, 'board_8_textures.png')); print('board_8_textures.png', S.size)
grid([(p('ref', '_sheet.jpg'), 'reference photos (Commons) the textures are painted from')], 1, 1800, 'board_9_refs.png')
