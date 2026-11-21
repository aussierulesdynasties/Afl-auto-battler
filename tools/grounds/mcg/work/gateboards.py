# Gate boards from the finished renders: signs (reference crop above the render), corners (corner close views,
# the two facade corner zooms, orbit frames). python work/gateboards.py <review_dir> <out_dir>
import sys, os
from PIL import Image, ImageDraw
RV, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
MCC = 'sg/at_-28.4_47.2_10_-53.0_88.2_17.5_32.png'; WAR = 'sg/at_0.0_-54.2_10_0.0_-102.0_17.5_32.png'
CORN = ['sg/at_190.7_-18.4_14_146.6_1.3_12_40.png', 'sg/at_-9.4_179.9_14_-21.1_133.5_12_40.png',
        'sg/at_163.3_118.6_14_116.6_105.0_12_40.png']


def fitw(im, w): return im.resize((w, max(1, int(im.size[1] * w / im.size[0]))))


def stack(items, w, out):
    """items: (label, image) pairs stacked top to bottom, each scaled to width w with a label bar"""
    ims = [(t, fitw(i.convert('RGB'), w)) for t, i in items]; H = sum(i.size[1] + 22 for _, i in ims)
    B = Image.new('RGB', (w, H), (16, 16, 16)); d = ImageDraw.Draw(B); y = 0
    for t, i in ims: d.text((6, y + 5), t, fill=(255, 230, 0)); B.paste(i, (0, y + 22)); y += i.size[1] + 22
    B.save(out); print(out, B.size)


def grid(items, cols, cw, out):
    ims = [(t, fitw(i.convert('RGB'), cw)) for t, i in items]; rh = max(i.size[1] for _, i in ims) + 22
    rows = (len(ims) + cols - 1) // cols; B = Image.new('RGB', (cols * (cw + 6), rows * rh), (16, 16, 16)); d = ImageDraw.Draw(B)
    for k, (t, i) in enumerate(ims):
        x, y = (k % cols) * (cw + 6), (k // cols) * rh; d.text((x + 6, y + 5), t, fill=(255, 230, 0)); B.paste(i, (x, y + 22))
    B.save(out); print(out, B.size)


o = lambda p: Image.open(p)
stack([('MCC sign reference: commons "MCC 050425.jpg" (CC0), crop', o('signref/crop_mcc.png')),
       ('MCC sign reference: commons members-stand photo (CC BY-SA 4.0), crop', o('signref/w2_sign.png')),
       ('MCC sign in the model (hand-drawn, model/signs.py), members upper tier ~329 deg', o(MCC)),
       ('SHANE WARNE STAND reference: commons "Shane Warne Stand unveiling.jpg" (CC BY-SA 4.0), crop', o('signref/w3_sign.png')),
       ('SHANE WARNE STAND in the model (hand-drawn), southern top tier ~180 deg', o(WAR))], 1360, OUT + '/board_signs.png')
# MCC seats close-up beside the photo, and an empty-seat close-up (lower half of the close views: seats only)
m = o(MCC).convert('RGB'); w_ = o(WAR).convert('RGB')
stack([('MCC members seats, photo: commons "MCC 050425.jpg" (CC0): mossy teal-green seats, white risers and walkway bands, black rails', o('signref/s02.jpg')),
       ('MCC members seats, model close-up', m)], 1360, OUT + '/board_mcc.png')
stack([('Empty seats close-up: members (MCC) side, model', m.crop((480, 560, 1440, 1080))),
       ('Empty seats close-up: southern stand, model', w_.crop((480, 560, 1440, 1080)))], 1360, OUT + '/board_empty_seats.png')
cz = [('corner view %d: %s' % (k + 1, os.path.basename(p)[:-4]), o(p)) for k, p in enumerate(CORN)]
cz += [('facade corner zoom: %s' % n, o(os.path.join(RV, n + '.png'))) for n in ('facade_020_north_windows', 'facade_314_nw_dark', 'facade_077_east_tower', 'facade_115_east_tower2')]
cz += [('orbit frame %s' % f, o(os.path.join(RV, 'orbit', f + '.png'))) for f in ('f000', 'f030', 'f060', 'f090')]
grid(cz, 2, 960, OUT + '/board_corners.png')
