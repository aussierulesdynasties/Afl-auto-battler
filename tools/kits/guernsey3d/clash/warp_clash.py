"""Fit a club's clash guernsey photos onto the club's own home cut, so the clash design covers exactly the
cloth the home cut has (its armholes, neck, hem), as the home photo did.

    python warp_clash.py CODE front_armpit_row back_armpit_row

Work folder: ref_raw/CODE_front.png, ref_raw/CODE_back.png (the shop photos) and uv/uv_CODE.json (the cut's
front and back triangles in the atlas square: dump_uv.gd). The rows are the photo's armpit (the bottom
of the armhole), read by eye on a pixel grid.

Rows: the photo's shoulder top, armpit and hem land on the cut's (piecewise straight between them). Across:
each row's left and right edge land on the cut's edges at that row, so the armhole binding follows the
cut's armhole. Both edge curves are smoothed down the rows, so a crease in the photo's outline doesn't
ripple the design. Writes ref/CODE_side.png (the photo in the cut's square, white outside), mask/CODE_side.png
(the cut's cloth) and wcheck_CODE.png (photo outline in red over the cut's, for the eye)."""
import sys, os, json, numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from norm_clash import flat, cloth

N = 2000


def cut_mask(code, side):
    T = np.array(json.load(open(f'uv/uv_{code}.json'))[side], float).reshape(-1, 3, 2)
    m = np.zeros((N, N), np.uint8)
    cv2.fillPoly(m, [np.round(t * N * 4).astype(np.int32) for t in T], 1, shift=2)
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0


def edges(m, rows):
    L = np.array([np.nonzero(m[r])[0].min() if m[r].any() else np.nan for r in rows], float)
    R = np.array([np.nonzero(m[r])[0].max() if m[r].any() else np.nan for r in rows], float)
    ok = ~np.isnan(L)
    L = np.interp(rows, rows[ok], L[ok]); R = np.interp(rows, rows[ok], R[ok])
    return nd.gaussian_filter1d(L, 4), nd.gaussian_filter1d(R, 4)


def cut_armpit(H):
    """The cut's armhole bottom: where its outline steps in most sharply below the shoulders."""
    w = np.array([np.ptp(np.nonzero(H[r])[0]) if H[r].any() else 0 for r in range(N)], float)
    w = nd.uniform_filter1d(w, 5)
    best, by = -1, 0
    for r in range(550, 900):
        d = w[r] - w[r + 20]
        if d > best:
            best, by = d, r + 10
    return by


def top_row(m, arm):
    """The shoulders' top: the first row as wide as a third of the armpit row (a stray hanger loop or a
    pointed neck tip above it doesn't count)."""
    w = m.sum(1)
    return int(np.nonzero(w > w[arm] / 3)[0][0])


def hem_row(m):
    """The hem in the middle half of the garment (the sides curve up)."""
    cols = np.nonzero(m.any(0))[0]
    c0, c1 = cols.min(), cols.max()
    mid = range(int(c0 + 0.25 * (c1 - c0)), int(c0 + 0.75 * (c1 - c0)))
    return float(np.median([np.nonzero(m[:, c])[0].max() for c in mid]))


def warp(code, side, prow):
    a, alpha = flat(f'ref_raw/{code}_{side}.png')
    m = cloth(a, alpha)
    H = cut_mask(code, side)
    hr = np.nonzero(H.any(1))[0]
    # the armhole's bottom is one point on the body, front and back; the front's step in is the clear one
    ha = cut_armpit(cut_mask(code, 'front'))
    ht, hh = top_row(H, ha), hem_row(H)
    pr = np.nonzero(m.any(1))[0]
    pt, ph = top_row(m, prow), hem_row(m)
    # target row -> photo row (top, armpit, hem anchors; straight on past the ends)
    ty = np.array([ht, ha, hh], float); sy = np.array([pt, prow, ph], float)
    rows = np.arange(N)
    src_y = np.interp(rows, ty, sy)
    lo = rows < ht; src_y[lo] = pt + (rows[lo] - ht) * (prow - pt) / (ha - ht)
    hi = rows > hh; src_y[hi] = ph + (rows[hi] - hh) * (ph - prow) / (hh - ha)
    prows = np.arange(m.shape[0])
    pL, pR = edges(m, prows)
    cL, cR = edges(H, rows)
    sL = np.interp(src_y, prows, pL); sR = np.interp(src_y, prows, pR)
    # above the cut's top and below its hem the edges hold their last values
    cL = np.where(rows < ht, cL[ht], np.where(rows > hh, cL[int(hh)], cL))
    cR = np.where(rows < ht, cR[ht], np.where(rows > hh, cR[int(hh)], cR))
    X = np.arange(N, dtype=float)[None, :]
    mapx = (sL[:, None] + (X - cL[:, None]) / (cR - cL)[:, None] * (sR - sL)[:, None]).astype(np.float32)
    mapy = np.repeat(src_y[:, None], N, 1).astype(np.float32)
    img = np.where(m[..., None], a, 255).astype(np.uint8)
    out = cv2.remap(img, mapx, mapy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    pm = cv2.remap(m.astype(np.uint8), mapx, mapy, cv2.INTER_NEAREST, borderValue=0) > 0
    os.makedirs('ref', exist_ok=True); os.makedirs('mask', exist_ok=True)
    Image.fromarray(out).save(f'ref/{code}_{side}.png')
    Image.fromarray((H * 255).astype(np.uint8)).save(f'mask/{code}_{side}.png')
    ck = out.copy()
    ck[H & ~nd.binary_erosion(H, iterations=3)] = (0, 160, 255)
    ck[pm & ~nd.binary_erosion(pm, iterations=2)] = (255, 0, 0)
    ck[int(ha)] = (0, 200, 0)
    print(code, side, 'cut top %d armpit %d hem %.0f | photo top %d armpit %d hem %.0f' % (ht, ha, hh, pt, prow, ph),
          '| photo cloth off the cut %.1f%%, cut bare %.1f%%' % (100 * (pm & ~H).sum() / H.sum(), 100 * (H & ~pm).sum() / H.sum()))
    return Image.fromarray(ck).resize((700, 700))


if __name__ == '__main__':
    code = sys.argv[1]
    s = Image.new('RGB', (1400, 700))
    for i, side in enumerate(('front', 'back')):
        s.paste(warp(code, side, int(sys.argv[2 + i])), (i * 700, 0))
    s.save(f'wcheck_{code}.png')
