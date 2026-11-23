"""Optus Stadium's bronze cladding, redrawn (Optus rebuild to the MCG standard, stage 3).

The facade's signature: horizontal anodised-aluminium fins (geometry, build.py) over a dark charcoal-slate base,
crossed by long thin streaks one fin high, 6-13 m long, in pale grey-white and terracotta copper-red (measured on
Google Earth's east and south views, 2026-11-23).

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
from glb_images import read_glb, replace_images, write_glb, _view_bytes  # noqa: E402

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

# The fin colours (sRGB). Measured 2026-11-23 on Google Earth's east view (f000, lit, 0.066 m a pixel) and south view
# (f270, shade): a dark charcoal-slate base, nearly uniform, crossed by long thin streaks one fin high, 6-13 m long:
# pale grey-white ones and terracotta copper-red ones. No mid-tone runs and no blue: the earlier passes drew short runs
# across the whole tone scale, which read as brickwork (PC GPU capture 2026-11-22).
BASE = np.array([(105, 110, 117), (117, 120, 123), (127, 127, 127), (120, 113, 110)], float)
PALE = np.array([(185, 187, 187), (202, 202, 200), (165, 167, 169)], float)
# 2026-11-23: the base lifted 1.1x more after 175b3d4c (12 views 0.70-0.94 of Google Earth, median 0.85), and before
# that another 1.2x once the streaks' occlusion reached the match (shaded views 0.68-0.80 of
# Google Earth's brightness, lit 0.80-0.87). Before that: the tile lifted 1.32x overall (base 1.46x, streaks 1.1x, since our streaks already stood out more than
# Google Earth's), Google Earth's brightness over our capture's at 236 facade hovers 18-30 m up
# on the 12 matched views, both lit by Google Earth's sun (survey/sun.json); the hue gap is Google Earth's haze.
COPPER_RED = np.array([(165, 101, 88), (178, 114, 99), (147, 92, 81)], float)
BASE_RM = (0.55, 0.3)   # (roughness, metalness), the whole bronze
SHADE_K = 1.1           # a streak in shade, over the base (Google Earth's shaded views: p90/p50 1.08-1.14)
P_PALE, P_RED = 0.13, 0.08   # the share of each fin row's length that is a streak of each kind


def _layout(seed=5):
    """Per row: run boundaries in s over one tile (periodic), and each run's kind (0 base, 1 pale, 2 red) and tone."""
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(ROWS):
        cuts = [rng.uniform(0, 6)]
        kinds = []
        while True:
            # Base runs between streaks; a streak mostly 6-13 m long (Google Earth), now and then a short one.
            # Run odds chosen so the streaks cover P_PALE and P_RED of the length (checked by shares()).
            kind = int(rng.choice(3, p=[0.748, 0.156, 0.096]))
            kinds.append(kind)
            ln = rng.uniform(6.0, 13.0) if kind and rng.random() < 0.75 else (rng.uniform(1.5, 5.0) if kind else rng.uniform(4.0, 16.0))
            nxt = cuts[-1] + ln
            if nxt >= BAY2 + cuts[0]:
                break
            cuts.append(nxt)
        cuts = np.array(cuts + [cuts[0] + BAY2])   # the last run wraps round to meet the first
        n = len(cuts) - 1
        rows.append({
            "cuts": cuts,
            "kind": np.array(kinds[:n]),
            "tone": rng.integers(0, 3, n),
            "base": rng.integers(0, len(BASE), n),
            "shine": rng.uniform(-0.04, 0.04, n),
        })
    return rows


ROWS_L = _layout()


def shares():
    """The share of fin length that is base, pale and red streak, over one tile."""
    t = np.zeros(3)
    for L in ROWS_L:
        np.add.at(t, L["kind"], np.diff(L["cuts"]))
    return t / t.sum()


def drift(s, d):
    """Soft diagonal drifts of lighter and darker tone, periodic over the tile (-1 .. 1)."""
    a = 2 * np.pi * s / BAY2
    b = 2 * np.pi * d / BH
    return (0.55 * np.sin(a + 2 * b + 0.7) + 0.3 * np.sin(2 * a - b + 2.1) + 0.25 * np.sin(3 * a + 3 * b + 4.0)) / 1.1


def colour(s, d, finish=False):
    """sRGB (H, W, 3) for arrays s (W) and d (H) in metres; finish=True gives the metal-roughness map instead."""
    s = np.mod(s, BAY2)
    S, D = np.meshgrid(s, np.mod(d, BH))
    pitch = BH / ROWS
    r = (D // pitch).astype(int) % ROWS
    t = (D % pitch) / pitch                      # 0 at the fin's top edge, 1 at its foot
    out = np.zeros(S.shape + (3,), float)
    kinds = np.zeros(S.shape, int)
    rng = np.random.default_rng(9)
    for ri in range(ROWS):
        m = r == ri
        if not m.any():
            continue
        L = ROWS_L[ri]
        ss = S[m]
        ss = np.where(ss < L["cuts"][0], ss + BAY2, ss)
        k = np.clip(np.searchsorted(L["cuts"], ss, side="right") - 1, 0, len(L["kind"]) - 1)
        kind = L["kind"][k][:, None]
        c = BASE[L["base"][k]] * (1.0 + 0.06 * drift(ss, D[m]))[:, None]
        c = np.where(kind == 1, PALE[L["tone"][k]], c)
        c = np.where(kind == 2, COPPER_RED[L["tone"][k]], c)
        c = c * (1.0 + L["shine"][k][:, None])
        # Along each run a slight fall-off from its middle (the fin's curvature catching the light).
        u = (ss - L["cuts"][k]) / np.maximum(L["cuts"][k + 1] - L["cuts"][k], 1e-3)
        c = c * (1.0 + 0.04 * np.sin(np.pi * u))[:, None]
        # Fin profile, gentle: the fins are geometry (build.py), so the texture only darkens the gap under each.
        tt = t[m][:, None]
        c = c * np.where(tt > 0.86, 0.75, 1.0)
        out[m] = c
        kinds[m] = kind[:, 0]
    # Brushed grain along the fins.
    grain = rng.normal(0, 1, (S.shape[0], max(8, S.shape[1] // 24)))
    grain = np.asarray(Image.fromarray(((grain * 20) + 128).clip(0, 255).astype(np.uint8)).resize(
        (S.shape[1], S.shape[0]), Image.BILINEAR), float) / 128.0 - 1.0
    out *= (1.0 + 0.03 * grain)[..., None]
    if finish:
        # glTF occlusion-metal-roughness (red occlusion, green roughness, blue metalness). Google Earth's streaks stand
        # out on the lit side (p90/p50 1.5) and all but vanish in shade (1.1); a plain streak keeps its 1.6 in shade.
        # Occlusion dims only the sky's light, never the sun's, so each streak pixel gets the occlusion that brings it
        # to 1.1x the base in shade, and keeps its full brightness in sun. (Metal streaks, tried first, changed nothing.)
        lin = lambda x: (np.clip(x, 0, 255) / 255.0) ** 2.2
        lum = lambda x: (lin(x) * np.array([0.2126, 0.7152, 0.0722])).sum(-1)
        lb = float(lum(BASE.mean(0)))
        mr = np.zeros(S.shape + (3,), np.uint8)
        mr[..., 0] = np.where(kinds > 0, np.clip(SHADE_K * lb / np.maximum(lum(out), 1e-4), 0, 1), 1.0) * 255
        mr[..., 1] = BASE_RM[0] * 255
        mr[..., 2] = BASE_RM[1] * 255
        return mr
    return np.clip(out, 0, 255).astype(np.uint8)


def tile(finish=False):
    w, h = int(round(BAY2 * PX)), int(round(BH * PX))
    s = (np.arange(w) + 0.5) / w * BAY2
    d = (np.arange(h) + 0.5) / h * BH
    return Image.fromarray(colour(s, d, finish), "RGB")


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


def sign_finish(old):
    """The finish map under the name sign; the letters take no occlusion (placed as in sign())."""
    w, h = int(round(SIGN_W * PX)), int(round(SIGN_DROP * PX))
    s = 7.3 + (np.arange(w) + 0.5) / w * SIGN_W
    d = (np.arange(h) + 0.5) / h * SIGN_DROP
    mr = colour(s, d, True).astype(float)
    alpha, _ = letters(old)
    lh, lw = alpha.shape[:2]
    y0 = int(round(LETTERS_D * PX - lh / 2))
    x0 = (w - lw) // 2
    sub = mr[y0:y0 + lh, x0:x0 + lw, 0]
    mr[y0:y0 + lh, x0:x0 + lw, 0] = sub * (1 - alpha[..., 0]) + 255 * alpha[..., 0]
    return Image.fromarray(mr.clip(0, 255).astype(np.uint8), "RGB")


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
    pale blue-teal grey glazing in 2.2 m floors under the 3.4 m glass head (frames are geometry, build.py)."""
    w, h = 1024, int(GLASS_H * 32)
    d = (np.arange(h)[:, None] + 0.5) / 32.0 * np.ones((1, w))
    u = (np.arange(w)[None, :] + 0.5) / w * np.ones((h, 1))
    img = np.zeros((h, w, 3))
    base = np.array((86, 109, 118), float)   # 2026-11-23: (100,128,138) / 1.17, our capture's brightness over Google Earth's at 128 glass-band hovers
    f = ((d - 3.8) % 2.2) / 2.2                                 # 0 at a floor's top, 1 at its foot
    img[:] = base * (1.08 - 0.22 * f)[..., None]
    img *= (1.0 + 0.05 * _noise(h, w, (12, 40), 3))[..., None]
    # The head rail, the louvre band at each floor's foot and the mullions are geometry now (build.py); the dark
    # strip and its posts above the glass head are modelled too, so the glass carries only its own tone.
    return Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB")


def entrance():
    """The street-level glazing, one entrance bay wide, ENTRANCE_H tall from the ground (Google Earth 060, 090): pale
    green glass, doors darker at the foot (its transoms and posts are geometry, build.py)."""
    w, h = 512, int(ENTRANCE_H * 32)
    z = (ENTRANCE_H - (np.arange(h)[:, None] + 0.5) / 32.0) * np.ones((1, w))   # image bottom is the ground
    u = (np.arange(w)[None, :] + 0.5) / w * np.ones((h, 1))
    t = (z % 2.5) / 2.5
    img = np.array((104, 132, 140), float) * (0.94 + 0.12 * t)[..., None]
    img = np.where((z < 2.6)[..., None], np.array((84, 100, 100), float), img)            # doors in shade
    # transoms and the posts between bays are geometry (build.py)
    img *= (1.0 + 0.05 * _noise(h, w, (8, 12), 4))[..., None]
    return Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB")


def storey():
    """The glazed storey under the bronze round the north and west (Google Earth 000, 330): dark blue glass with sky
    caught low (its posts, mullions and head rail are geometry, build.py); image top at 13.5 m, 6 m."""
    w, h = 1024, 192
    d = (np.arange(h)[:, None] + 0.5) / h * 6.0 * np.ones((1, w))
    u = (np.arange(w)[None, :] + 0.5) / w * np.ones((h, 1))
    img = np.array((44, 58, 78), float) * (0.9 + 0.35 * (d / 6.0))[..., None]
    img *= (1.0 + 0.06 * _noise(h, w, (4, 24), 5))[..., None]
    # mullions, posts and the head rail are geometry (build.py)
    return Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB")


def roof():
    """The roof membrane, one bay across (u) and fascia (image top) to inner edge (image bottom), Google Earth roof_S and
    roof_top: white PTFE pillows, shaded toward the valleys where a grey cable line runs, two faint cross cables, a grey
    translucent strip along the inner edge (the seats' shadow through it) and a white rim."""
    w, h = 256, 1024
    u = (np.arange(w)[None, :] + 0.5) / w * np.ones((h, 1))
    v = (np.arange(h)[:, None] + 0.5) / h * np.ones((1, w))
    img = np.array((246, 246, 243), float) * (0.88 + 0.12 * np.sin(np.pi * u) ** 0.6)[..., None]
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
    g = np.array((212, 214, 216), float) * (1.0 + 0.03 * _noise(64, 64, (4, 4), 8))[..., None]
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
    new = {"bronze": tile(), "sign_a": sign(old), "glass": glass(), "entrance": entrance(), "storey": storey(), "roof": roof(), "steel": steel(),
           "bronze_mr": tile(True), "sign_a_mr": sign_finish(old)}
    if "--preview" in sys.argv:
        p = sys.argv[sys.argv.index("--preview") + 1]
        for n, im in new.items():
            im.save(p.replace(".png", "_%s.png" % n))
        return
    # build.py reads the finish maps from tex/ (it needs them to give the materials their metal-roughness texture).
    for n in ("bronze_mr", "sign_a_mr"):
        new[n].save(os.path.join(REPO, ".claude", "review", "optus", "tex", n + ".png"))
    replace_images(GLB, {n: png(im) for n, im in new.items() if n in names})
    # The finish maps' red channel is the occlusion: point each bronze material's occlusion at its own map.
    js, bn = read_glb(GLB)
    for m in js["materials"]:
        mrt = m.get("pbrMetallicRoughness", {}).get("metallicRoughnessTexture")
        if m.get("name") in ("bronze", "sign_a") and mrt:
            m["occlusionTexture"] = {"index": mrt["index"]}
    write_glb(GLB, js, bn)
    print({n: im.size for n, im in new.items()})


if __name__ == "__main__":
    main()
