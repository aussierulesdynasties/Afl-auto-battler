"""Optus Stadium's bronze cladding, redrawn (Optus rebuild to the MCG standard, stage 3).

The facade's signature: horizontal anodised-aluminium fins in mixed bronze, copper, chocolate and
sand tones, in runs of 1 to 6 m, with the odd deep copper-red run and thin pale-blue slivers lit
through the gaps; soft diagonal drifts of lighter and darker tone across the whole drum (the
director's sunset photo, /mnt/project-files/optus-rebuild/ref_facade_sunset.jpg, and Google Earth).

Draws one pattern in metres round the drum (s, along the facade from segment 0) and down from the
bronze's top (d), so the plain bronze and the two name signs join without a seam, and writes them
into assets/grounds/optus/optus.glb:

- `bronze`: one tile, 2 bays (32.51 m) by 20.65 m (the model's UVs: u = s / 32.51, v = d / 20.65),
  48 px a metre.
- `sign_a`: the bronze behind every name sign (tools/grounds/optus/facade.json: 19 segments wide, 32 m down
  from the bronze's top), with the letters lifted from #1867's sign (white OPTUS STADIUM, yellow "yes") set
  6 m under the top, as on the real drum.
- `glass`: the glass band over the bronze (no white Y columns outside, Google Earth) `entrance`: the street glazing,
  and `storey`: the glazed storey under the bronze round the north and west (also saved as tex/storey.png for build.py);
  `roof` (one bay a tile, build.py) and `steel` (the trusses), also saved to tex/ for build.py.

    python3 tools/grounds/optus/bronze.py [--old-sign sign_a.png] [--preview out.png]
"""
import io
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from glb_images import read_glb, replace_images, _view_bytes  # noqa: E402

REPO = os.path.join(HERE, "..", "..", "..")
GLB = os.path.join(REPO, "assets", "grounds", "optus", "optus.glb")

PX = 48.0                 # pixels a metre
BAY2 = 32.508388867793855  # the bronze tile's width round the drum (2 bays, build.py BAY2)
BH = 20.65                 # its height (tex/info.json bronze_h_m)
ROWS = 66                  # fins in one tile height: 0.313 m apart
SIGN_W = 38.6              # 19 of the drum's 416 segments
SIGN_DROP = 32.0
LETTERS_D = 6.0            # the letters' middle, metres under the bronze's top
OLD_SIGN = (37.28464798665914, 32.0)   # #1867's sign_a in metres (its letters are lifted from it)

# The fin colours (sRGB) and how often each is drawn; the low-frequency drift picks lighter or darker.
# Google Earth's north and east close views (2026-11-21): a dark chocolate base with long, thin, high-contrast runs of
# copper, salmon and pale pinkish sand, so the fins still read as streaks from across the river.
TONES = np.array([
    (64, 52, 48), (78, 60, 54), (94, 68, 56), (98, 66, 52), (118, 78, 60),
    (140, 92, 70), (162, 108, 84), (184, 130, 106), (204, 160, 140),
], float)
COPPER_RED = np.array([(170, 96, 78), (186, 112, 92), (150, 80, 62)], float)
BLUE = np.array((128, 190, 222), float)


def _layout(seed=5):
    """Per row: run boundaries in s over one tile (periodic), and each run's tone, red and blue flags."""
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(ROWS):
        cuts = [rng.uniform(0, 3)]
        while cuts[-1] < BAY2 + cuts[0]:
            cuts.append(cuts[-1] + rng.choice([rng.uniform(0.8, 2.2), rng.uniform(2.0, 4.5), rng.uniform(4.0, 7.0)],
                                              p=[0.45, 0.4, 0.15]))
        # The last run wraps round to meet the first.
        cuts = np.array(cuts[:-1] + [cuts[0] + BAY2])
        n = len(cuts) - 1
        rows.append({
            "cuts": cuts,
            # Most runs sit back in the dark base; under half catch the light as copper, salmon or sand streaks.
            "jit": np.where(rng.random(n) < 0.58, rng.normal(-2.4, 0.6, n), rng.normal(1.9, 1.3, n)),           # each run's own step up or down the tone scale
            "red": rng.random(n) < 0.08,
            "red_i": rng.integers(0, len(COPPER_RED), n),
            "blue": rng.random(n) < 0.015,
            "shine": rng.uniform(-0.05, 0.05, n),
        })
    return rows


ROWS_L = _layout()


def drift(s, d):
    """Soft diagonal drifts of lighter and darker tone, periodic over the tile (-1 .. 1)."""
    a = 2 * np.pi * s / BAY2
    b = 2 * np.pi * d / BH
    return (0.55 * np.sin(a + 2 * b + 0.7) + 0.3 * np.sin(2 * a - b + 2.1) + 0.25 * np.sin(3 * a + 3 * b + 4.0)) / 1.1


def colour(s, d):
    """sRGB (H, W, 3) for arrays s (W) and d (H) in metres."""
    s = np.mod(s, BAY2)
    S, D = np.meshgrid(s, np.mod(d, BH))
    pitch = BH / ROWS
    r = (D // pitch).astype(int) % ROWS
    t = (D % pitch) / pitch                      # 0 at the fin's top edge, 1 at its foot
    out = np.zeros(S.shape + (3,), float)
    rng = np.random.default_rng(9)
    for ri in range(ROWS):
        m = r == ri
        if not m.any():
            continue
        L = ROWS_L[ri]
        ss = S[m]
        ss = np.where(ss < L["cuts"][0], ss + BAY2, ss)
        k = np.clip(np.searchsorted(L["cuts"], ss, side="right") - 1, 0, len(L["jit"]) - 1)
        level = 3.0 + 1.1 * drift(ss, D[m]) + L["jit"][k]
        lo = np.clip(np.floor(level).astype(int), 0, len(TONES) - 2)
        f = np.clip(level - lo, 0, 1)[:, None]
        c = TONES[lo] * (1 - f) + TONES[lo + 1] * f
        c = np.where(L["red"][k][:, None], COPPER_RED[L["red_i"][k]], c)
        c = c * (1.0 + L["shine"][k][:, None])
        # Along each run a slight fall-off from its middle (the fin's curvature catching the light).
        a0 = L["cuts"][k]
        a1 = L["cuts"][k + 1]
        u = (ss - a0) / np.maximum(a1 - a0, 1e-3)
        c = c * (1.0 + 0.05 * np.sin(np.pi * u))[:, None]
        tt = t[m][:, None]
        # Fin profile: a bright lip, the face, and the dark gap under it.
        prof = np.where(tt < 0.07, 1.16, np.where(tt > 0.86, 0.38, 1.0 - 0.10 * tt))
        # A lit run catches the light on its upper face only; its lower half falls back to the dark base, so each
        # streak reads thin, as on the drum.
        lit = (L["jit"][k] > 0) & (tt[:, 0] > 0.5) & ~L["red"][k]
        c = np.where(lit[:, None], TONES[1] * (1.0 + L["shine"][k][:, None]), c)
        c = c * prof
        # Pale-blue slivers: the light strip in the gap, thin and short.
        blue = L["blue"][k] & (tt[:, 0] > 0.64) & (tt[:, 0] < 0.9) & (u > 0.1) & (u < 0.9)
        c = np.where(blue[:, None], BLUE, c)
        out[m] = c
    # Brushed grain along the fins.
    grain = rng.normal(0, 1, (S.shape[0], max(8, S.shape[1] // 24)))
    grain = np.asarray(Image.fromarray(((grain * 20) + 128).clip(0, 255).astype(np.uint8)).resize(
        (S.shape[1], S.shape[0]), Image.BILINEAR), float) / 128.0 - 1.0
    out *= (1.0 + 0.035 * grain)[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def tile():
    w, h = int(round(BAY2 * PX)), int(round(BH * PX))
    s = (np.arange(w) + 0.5) / w * BAY2
    d = (np.arange(h) + 0.5) / h * BH
    return Image.fromarray(colour(s, d), "RGB")


def letters(old):
    """The letters of #1867's sign, cropped to their box: alpha and colour, at PX pixels a metre."""
    a = np.asarray(old.convert("RGB"), float)
    white = (a.min(-1) > 196) & (a.max(-1) - a.min(-1) < 40)
    yellow = (a[..., 0] > 190) & (a[..., 1] > 130) & (a[..., 2] < 110) & (a[..., 0] - a[..., 2] > 110)
    m = (white | yellow)
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min() - 4, ys.max() + 5, xs.min() - 4, xs.max() + 5
    mi = Image.fromarray(m.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(3)).crop((x0, y0, x1, y1))
    col = np.where(yellow[..., None], np.array((240, 186, 40), float), np.array((244, 244, 240), float))
    ci = Image.fromarray(col.astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).crop((x0, y0, x1, y1))
    k = PX / (old.size[0] / OLD_SIGN[0])
    size = (int(round(mi.size[0] * k)), int(round(mi.size[1] * k)))
    mi = mi.resize(size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    ci = ci.resize(size, Image.LANCZOS)
    return np.asarray(mi, float)[..., None] / 255.0, np.asarray(ci, float)


def sign(old):
    w, h = int(round(SIGN_W * PX)), int(round(SIGN_DROP * PX))
    s = 7.3 + (np.arange(w) + 0.5) / w * SIGN_W
    d = (np.arange(h) + 0.5) / h * SIGN_DROP
    img = colour(s, d).astype(float)
    alpha, col = letters(old)
    lh, lw = alpha.shape[:2]
    y0 = int(round(LETTERS_D * PX - lh / 2))
    x0 = (w - lw) // 2
    sub = img[y0:y0 + lh, x0:x0 + lw]
    img[y0:y0 + lh, x0:x0 + lw] = sub * (1 - alpha) + col * alpha
    return Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB")


GLASS_H = 30.0        # build.py GH: the glass band's UV drop from the roof's soffit (image top) downward
ENTRANCE_H = 16.0     # build.py EH: the street glazing's UV height from the ground (image bottom) upward


def _noise(h, w, cells, seed):
    g = np.random.default_rng(seed).normal(0, 1, cells)
    return np.asarray(Image.fromarray(((g * 40) + 128).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC),
                      float) / 128.0 - 1.0


def glass():
    """The glass band over the bronze, one tile 2 bays wide (u) and GLASS_H down from the soffit (Google Earth 060/000):
    a dark open strip 4.2 m deep with a slim white post each bay under the roof's fascia, a white head rail, then pale
    grey-green glazing in 2.2 m floors, each with a bright louvre band at its foot and faint mullions every 1.55 m."""
    w, h = 1024, int(GLASS_H * 32)
    d = (np.arange(h)[:, None] + 0.5) / 32.0 * np.ones((1, w))
    u = (np.arange(w)[None, :] + 0.5) / w * np.ones((h, 1))
    img = np.zeros((h, w, 3))
    base = np.array((150, 172, 160), float)
    f = ((d - 4.6) % 2.2) / 2.2                                 # 0 at a floor's top, 1 at its foot
    img[:] = base * (1.08 - 0.22 * f)[..., None]
    img = np.where((f > 0.8)[..., None], np.array((230, 236, 230), float), img)           # louvre band
    img = np.where((f > 0.95)[..., None], np.array((112, 128, 122), float), img)          # its shadow
    mull = (np.abs(((u * 20) % 1) - 0.5) > 0.47)
    img = np.where(mull[..., None], img * 0.9 + 18, img)
    img *= (1.0 + 0.05 * _noise(h, w, (12, 40), 3))[..., None]
    strip = d < 4.2
    img[strip] = np.array((44, 50, 54), float) * (1.0 + 0.25 * (d[strip] / 4.2))[..., None]
    post = strip & ((np.abs(((u * 2) % 1) - 0.5) > 0.5 - 0.35 / 32.5))
    img[post] = (226, 228, 226)
    img[(d >= 4.2) & (d < 4.6)] = (224, 226, 224)                                          # head rail
    return Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB")


def entrance():
    """The street-level glazing, one entrance bay wide, ENTRANCE_H tall from the ground (Google Earth 060, 090): pale
    green glass in 2.5 m transoms with slim white mullions every quarter bay, doors darker at the foot."""
    w, h = 512, int(ENTRANCE_H * 32)
    z = (ENTRANCE_H - (np.arange(h)[:, None] + 0.5) / 32.0) * np.ones((1, w))   # image bottom is the ground
    u = (np.arange(w)[None, :] + 0.5) / w * np.ones((h, 1))
    t = (z % 2.5) / 2.5
    img = np.array((128, 154, 150), float) * (0.94 + 0.12 * t)[..., None]
    img = np.where((z < 2.6)[..., None], np.array((84, 100, 100), float), img)            # doors in shade
    img = np.where((t < 0.04)[..., None] & (z > 0.3)[..., None], np.array((210, 214, 212), float), img)
    mull = np.abs(((u * 4) % 1) - 0.5) > 0.5 - 0.12 / 3.6
    img[mull] = (222, 224, 222)
    img *= (1.0 + 0.05 * _noise(h, w, (8, 12), 4))[..., None]
    return Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB")


def storey():
    """The glazed storey under the bronze round the north and west (Google Earth 000, 330): dark blue glass with sky
    caught low, slim white posts four to a tile (2 bays, about 8 m apart), a white head rail; image top at 13.5 m, 6 m."""
    w, h = 1024, 192
    d = (np.arange(h)[:, None] + 0.5) / h * 6.0 * np.ones((1, w))
    u = (np.arange(w)[None, :] + 0.5) / w * np.ones((h, 1))
    img = np.array((44, 58, 78), float) * (0.9 + 0.35 * (d / 6.0))[..., None]
    img *= (1.0 + 0.06 * _noise(h, w, (4, 24), 5))[..., None]
    img[np.abs(((u * 16) % 1) - 0.5) > 0.5 - 0.05 / 2.0] = (70, 86, 104)        # mullions
    img[np.abs(((u * 4) % 1) - 0.5) > 0.5 - 0.3 / 8.1] = (226, 228, 226)        # posts
    img[d < 0.25] = (222, 224, 222)
    return Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB")


def roof():
    """The roof membrane, one bay across (u) and fascia (image top) to inner edge (image bottom), Google Earth roof_S and
    roof_top: white PTFE pillows, shaded toward the valleys where a grey cable line runs, two faint cross cables, a grey
    translucent strip along the inner edge (the seats' shadow through it) and a white rim."""
    w, h = 256, 1024
    u = (np.arange(w)[None, :] + 0.5) / w * np.ones((h, 1))
    v = (np.arange(h)[:, None] + 0.5) / h * np.ones((1, w))
    img = np.array((246, 246, 243), float) * (0.82 + 0.18 * np.sin(np.pi * u) ** 0.6)[..., None]
    img *= (1.0 + 0.025 * _noise(h, w, (16, 4), 6))[..., None]
    for c in (0.36, 0.68):
        img[np.abs(v - c) < 0.0025] *= 0.9
    img[(u < 0.012) | (u > 0.988)] = (150, 154, 158)
    img[v > 0.9] = np.array((168, 174, 178), float) * (1.0 + 0.04 * _noise(h, w, (8, 4), 7))[v > 0.9][:, None]
    img[v > 0.985] = (238, 238, 236)
    img[v < 0.012] = (236, 236, 234)
    return Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB")


def steel():
    """The roof trusses' steel: light grey, so they read as Google Earth's grey spines along the valleys."""
    g = np.array((178, 182, 186), float) * (1.0 + 0.03 * _noise(64, 64, (4, 4), 8))[..., None]
    return Image.fromarray(g.clip(0, 255).astype(np.uint8), "RGB")


def png(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return b.getvalue()


def main():
    js, bn = read_glb(GLB)
    names = {im["name"] for im in js["images"]}
    src = sys.argv[sys.argv.index("--old-sign") + 1] if "--old-sign" in sys.argv else None
    old = Image.open(src) if src else Image.open(io.BytesIO(_view_bytes(
        js, bn, next(im for im in js["images"] if im["name"] == "sign_a")["bufferView"])))
    new = {"bronze": tile(), "sign_a": sign(old), "glass": glass(), "entrance": entrance(), "storey": storey(), "roof": roof(), "steel": steel()}
    if "--preview" in sys.argv:
        p = sys.argv[sys.argv.index("--preview") + 1]
        for n, im in new.items():
            im.save(p.replace(".png", "_%s.png" % n))
        return
    replace_images(GLB, {n: png(im) for n, im in new.items() if n in names})
    print({n: im.size for n, im in new.items()})


if __name__ == "__main__":
    main()
