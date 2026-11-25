"""Put a club's clash guernsey shop photos in the cut's frame (2000x2000), as norm2.py does for the home
photos: the armpit row (the bottom of the armhole) sits on body y 1.37 and the chest width there is the
body's own (905 px = 2 x 0.196 m at 2310 px a metre). The home cut is reused, so the clash design lands
on the same body the home design was fitted to.

    python norm_clash.py CODE [front_armpit_row back_armpit_row]

Without rows, each photo's armpit is found where its outline stops narrowing below the shoulders (the
side edges turn straight down), and a check image (check_CODE.png) marks the rows read, for the eye.
Photos: ref_raw/CODE_front.png and ref_raw/CODE_back.png (a shop photo on a plain studio background, or
a cut-out). Writes ref/CODE_front.png, ref/CODE_back.png and norm_CODE.json."""
import sys, json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

CHEST_PX, S_PX = 905.0, 2310.0


def flat(fn):
    im = Image.open(fn).convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    alpha = np.asarray(im)[..., 3]
    return np.asarray(Image.alpha_composite(bg, im).convert('RGB')).astype(float), alpha


def cloth(a, alpha):
    """The garment: a cut-out's opaque pixels, or everything not joined to the border through the studio
    background's colour (within 6 levels: a white guernsey's own edge is a shade off the white behind it)."""
    if (alpha < 128).mean() > 0.05:
        m = alpha >= 128
        lab2, n = nd.label(m)
        if n > 1:
            sizes = nd.sum(m, lab2, range(1, n + 1))
            m = lab2 == (1 + int(np.argmax(sizes)))
        return nd.binary_fill_holes(m)
    h, w, _ = a.shape
    edge = np.r_[a[0], a[-1], a[:, 0], a[:, -1]]
    ref = np.median(edge, 0)
    near = np.abs(a - ref).max(-1) < 6
    lab, _ = nd.label(near)
    ids = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    bg = np.isin(lab, list(ids))
    m = ~bg
    m = nd.binary_opening(m, iterations=2)
    lab2, n = nd.label(m)
    if n > 1:
        sizes = nd.sum(m, lab2, range(1, n + 1))
        m = lab2 == (1 + int(np.argmax(sizes)))
    return nd.binary_fill_holes(m)


def armpit(m):
    """The armhole's bottom on each side: below the shoulder's tip, the outline's side edge curves in round
    the armhole and then turns down the body; the turn is the sharpest bend of the edge (its slope changes
    most within 3% of the garment's height). The two sides' rows are averaged."""
    rows = np.nonzero(m.any(1))[0]
    top, bot = rows.min(), rows.max()
    H = bot - top
    ys = np.arange(top, bot + 1)
    xl = np.array([np.nonzero(m[r])[0].min() if m[r].any() else np.nan for r in ys], float)
    xr = np.array([np.nonzero(m[r])[0].max() if m[r].any() else np.nan for r in ys], float)
    k = max(3, int(0.03 * H))
    out = []
    for e, sgn in ((xl, 1.0), (xr, -1.0)):
        e = nd.uniform_filter1d(np.nan_to_num(e, nan=np.nanmean(e)), 5)
        tip = int(np.argmin(sgn * e[: int(0.35 * H)]))        # the shoulder's tip: the edge at its widest
        lo, hi = tip + k, int(0.62 * H)
        best, by = -1e9, lo
        for i in range(lo, hi):
            s_in = (e[i] - e[i - k]) * sgn                       # going in above
            s_dn = (e[i + k] - e[i]) * sgn                       # going in below
            bend = s_in - s_dn
            if bend > best:
                best, by = bend, i
        out.append(by)
    return top + int(round(np.mean(out))), top + out[0], top + out[1]


def main():
    c = sys.argv[1]
    rows = {}
    if len(sys.argv) > 3:
        rows = {'front': int(sys.argv[2]), 'back': int(sys.argv[3])}
    xf = {}
    checks = []
    for side in ('front', 'back'):
        a, alpha = flat(f'ref_raw/{c}_{side}.png')
        m = cloth(a, alpha)
        ap, l_, r_ = armpit(m) if side not in rows else (rows[side], 0, 0)
        w = np.median([np.ptp(np.nonzero(m[r])[0]) for r in range(ap, ap + 8)])
        cx = np.median([(lambda z: (z.min() + z.max()) / 2)(np.nonzero(m[r])[0]) for r in range(ap, ap + 8)])
        s = CHEST_PX / w
        arow = 189.0 + (1.62 - 1.37) * S_PX
        tx, ty = 1000 - cx * s, arow - ap * s
        im = Image.fromarray(np.where(m[..., None], a, 255).astype(np.uint8))
        out = im.transform((2000, 2000), Image.AFFINE, (1 / s, 0, -tx / s, 0, 1 / s, -ty / s),
                           resample=Image.BICUBIC, fillcolor=(255, 255, 255))
        out.save(f'ref/{c}_{side}.png')
        xf[side] = (s, s, tx, ty)
        rws = np.nonzero(m.any(1))[0]
        print(c, side, 'armpit', ap, '(sides %d %d)' % (l_, r_), 'chest px %.0f' % w, 'scale %.3f' % s, 'top -> %.0f' % (ty + rws.min() * s),
              'hem -> %.0f' % (ty + rws.max() * s))
        ck = out.copy()
        d = ImageDraw.Draw(ck)
        d.line([(0, arow), (2000, arow)], fill=(0, 200, 0), width=4)
        d.line([(1000 - CHEST_PX / 2, 0), (1000 - CHEST_PX / 2, 2000)], fill=(0, 120, 255), width=3)
        d.line([(1000 + CHEST_PX / 2, 0), (1000 + CHEST_PX / 2, 2000)], fill=(0, 120, 255), width=3)
        ck.thumbnail((700, 700))
        checks.append(ck)
    json.dump(xf, open(f'norm_{c}.json', 'w'))
    sheet = Image.new('RGB', (1400, 700), 'white')
    for i, ck in enumerate(checks):
        sheet.paste(ck, (i * 700, 0))
    sheet.save(f'check_{c}.png')


if __name__ == "__main__":
    main()
