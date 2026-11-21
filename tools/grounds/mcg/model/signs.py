# The ground's own name signs, drawn by hand in code (no photo pixels, no sponsors). Runs after paint4.py.
# Lettering: DejaVu Serif / DejaVu Sans (Bitstream Vera licence: free to use, embed and sell; ships with matplotlib).
# References (looked at, never sampled):
#  sign_mcc   - commons File:MCC 050425.jpg (CC0): white fascia band, navy serif capitals MELBOURNE CRICKET CLUB,
#               an MCC monogram at each end; front of the members' upper tier (length ~22 m from the seat count).
#  sign_warne - commons File:Shane Warne Stand unveiling.jpg (CC BY-SA 4.0): slate-blue band, white sans capitals
#               SHANE WARNE STAND, MCG emblem at each end; front of the southern top tier.
import os, json, math, numpy as np
import matplotlib
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'tex') + '/'
TILE = json.load(open(OUT + 'tiles.json'))
FD = os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data', 'fonts', 'ttf')
PPM = 120  # pixels per metre


def fit(d, text, font_path, h_px, w_px):
    s = h_px
    while s > 4:
        f = ImageFont.truetype(font_path, s); b = d.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= w_px: return f, b
        s -= 2
    return f, b


def spaced(d, text, font, cx, cy, width, fill):
    """letters spread evenly across `width` (the reference sign's letters are widely tracked)"""
    ws = [d.textbbox((0, 0), c, font=font)[2] for c in text]; gap = (width - sum(ws)) / max(1, len(text) - 1)
    x = cx - width / 2
    for c, w in zip(text, ws):
        d.text((x, cy), c, font=font, fill=fill, anchor='lm'); x += w + gap


def monogram(d, cx, cy, hpx):
    """MCC crest as on the fascia (commons MCC 050425.jpg): interlaced serif M C C, navy with red, no disc"""
    fm = ImageFont.truetype(os.path.join(FD, 'DejaVuSerif-Bold.ttf'), int(hpx * 0.72))
    fc = ImageFont.truetype(os.path.join(FD, 'DejaVuSerif.ttf'), int(hpx * 0.95))
    d.text((cx - hpx * 0.26, cy), 'C', font=fc, fill=(176, 38, 46), anchor='mm')
    d.text((cx + hpx * 0.26, cy), 'C', font=fc, fill=(176, 38, 46), anchor='mm')
    d.text((cx, cy), 'M', font=fm, fill=(30, 40, 84), anchor='mm', stroke_width=max(1, hpx // 40), stroke_fill=(236, 238, 236))


def words(d, ws, font, cx, cy, width, fill, space):
    """letters tracked evenly, a space of `space` px between words (as on the reference band)"""
    cw = [[d.textbbox((0, 0), c, font=font)[2] for c in w] for w in ws]; nl = sum(len(w) - 1 for w in ws)
    g = (width - sum(map(sum, cw)) - space * (len(ws) - 1)) / nl; x = cx - width / 2
    for w, c in zip(ws, cw):
        for k, (ch, cwid) in enumerate(zip(w, c)):
            d.text((x, cy), ch, font=font, fill=fill, anchor='lm'); x += cwid + (g if k < len(w) - 1 else 0)
        x += space


def sign_mcc(L=22.0, H=3.0):
    """the whole fascia height is the white band; letters ~0.9 m high, crests ~1.4 m, at both ends"""
    W, Hp = int(L * PPM), int(H * PPM); im = Image.new('RGB', (W, Hp), (236, 238, 236)); d = ImageDraw.Draw(im)
    d.rectangle((0, Hp - int(0.10 * PPM), W, Hp), fill=(206, 210, 212)); d.rectangle((0, 0, W, int(0.06 * PPM)), fill=(214, 216, 218))
    for x in np.arange(0, L, 2.4):  # panel joints
        d.line((x * PPM, 0, x * PPM, Hp), fill=(220, 222, 222), width=2)
    monogram(d, int(1.1 * PPM), Hp // 2, int(1.4 * PPM)); monogram(d, W - int(1.1 * PPM), Hp // 2, int(1.4 * PPM))
    f = ImageFont.truetype(os.path.join(FD, 'DejaVuSerif-Bold.ttf'), int(0.95 * PPM))
    words(d, ['MELBOURNE', 'CRICKET', 'CLUB'], f, W / 2, Hp / 2 + 4, (L - 4.6) * PPM, (32, 40, 78), 0.6 * PPM)
    im.save(OUT + 'sign_mcc.png'); TILE['sign_mcc'] = (L, H)


def sign_warne(L=28.0, H=1.6):
    """slate-blue band, white sans capitals ~70% of its height, a darker end panel with the MCG round emblem at each
    end (commons File:Shane Warne Stand unveiling.jpg, CC BY-SA 4.0; sponsor ribbons either side left out)"""
    W, Hp = int(L * PPM), int(H * PPM); im = Image.new('RGB', (W, Hp), (106, 122, 148)); d = ImageDraw.Draw(im)
    ep = int(1.6 * PPM)
    for x0 in (0, W - ep):
        d.rectangle((x0, 0, x0 + ep, Hp), fill=(78, 90, 110)); cx, cy, r = x0 + ep // 2, Hp // 2, int(0.42 * PPM)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(226, 230, 236), width=max(2, r // 8))
        d.ellipse((cx - r * 0.62, cy - r * 0.34, cx + r * 0.62, cy + r * 0.34), outline=(226, 230, 236), width=max(2, r // 10))
    d.rectangle((0, 0, W, int(0.05 * PPM)), fill=(70, 80, 98)); d.rectangle((0, Hp - int(0.05 * PPM), W, Hp), fill=(64, 74, 92))
    f = ImageFont.truetype(os.path.join(FD, 'DejaVuSans.ttf'), int(1.5 * PPM))
    words(d, ['SHANE', 'WARNE', 'STAND'], f, W / 2, Hp / 2 + 3, L * PPM - 2 * ep - int(1.2 * PPM), (236, 240, 246), 1.3 * PPM)
    im.save(OUT + 'sign_warne.png'); TILE['sign_warne'] = (L, H)


sign_mcc(); sign_warne()
json.dump(TILE, open(OUT + 'tiles.json', 'w'))
print('signs')
