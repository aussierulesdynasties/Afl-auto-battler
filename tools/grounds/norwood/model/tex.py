"""Norwood Oval's textures, painted by hand in numpy (no photo pixels): each one tiles, at 64 px a metre
for the close materials and 32 for the rest. Colours sampled from the January 2026 Commons photos and Google
Earth. Writes tex/<name>.png and tex/spec.json ({name: {img, tw, th}}, the tile's size in metres).

Only detail too small to model is painted: brick coursing and mortar, the ribs of corrugated sheeting,
board joints, concrete joints and weathering. Windows, reveals, bands and pilasters are geometry."""
import json
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tex")
rng = np.random.default_rng(7)
SPEC = {}


def save(name, a, tw, th, **kw):
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name + ".png"))
    SPEC[name] = dict(img=name + ".png", tw=tw, th=th, **kw)


def noise(h, w, scale, amp, seed=None):
    """Tileable value noise: a random grid at `scale` px, smoothly interpolated, wrapping."""
    r = np.random.default_rng(seed) if seed is not None else rng
    gh, gw = max(1, h // scale), max(1, w // scale)
    g = r.normal(0, 1, (gh, gw))
    y = np.arange(h) * gh / h
    x = np.arange(w) * gw / w
    y0, x0 = np.floor(y).astype(int), np.floor(x).astype(int)
    fy, fx = y - y0, x - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    y1, x1 = (y0 + 1) % gh, (x0 + 1) % gw
    a = g[y0][:, x0] * (1 - fx) + g[y0][:, x1] * fx
    b = g[y1][:, x0] * (1 - fx) + g[y1][:, x1] * fx
    return (a * (1 - fy)[:, None] + b * fy[:, None]) * amp


def fbm(h, w, amp, scales=(64, 24, 8, 3)):
    return sum(noise(h, w, s, amp / (i + 1)) for i, s in enumerate(scales))


def flat(name, rgb, tw=2.0, th=2.0, ppm=32, amp=6.0):
    h, w = int(th * ppm), int(tw * ppm)
    a = np.zeros((h, w, 3)) + np.array(rgb, float)
    a += fbm(h, w, amp)[..., None]
    save(name, a, tw, th)


def brick(name, base, mortar, tw=4.6, th=3.04, ppm=64, var=14, burnt=0.12):
    """Running-bond face brick: 230 x 76 mm bricks, 10 mm joints, each brick its own shade."""
    h, w = int(th * ppm), int(tw * ppm)
    a = np.zeros((h, w, 3))
    cw, ch = 0.24 * ppm, 0.086 * ppm
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    row = (yy / ch).astype(int)
    xs = xx + (row % 2) * cw / 2
    col = (xs / cw).astype(int)
    rows, cols = int(np.ceil(h / ch)) + 1, int(np.ceil(w / cw)) + 2
    shade = rng.normal(0, var, (rows, cols, 1)) + np.where(rng.random((rows, cols, 1)) < burnt, -28, 0)
    hue = rng.normal(0, 5, (rows, cols, 1)) * np.array([1.0, 0.4, 0.2])
    cols_w = int(round(w / cw))
    a[:] = np.array(base, float) + shade[row % rows, col % cols_w] + hue[row % rows, col % cols_w]
    jy = (yy % ch) < 0.012 * ppm + 0.5
    jx = (xs % cw) < 0.012 * ppm + 0.5
    m = jy | jx
    a[m] = np.array(mortar, float) + rng.normal(0, 4, (m.sum(), 1))
    a += fbm(h, w, 5)[..., None]
    save(name, a, tw, th)


def sheeting(name, base, tw=1.52, th=4.0, ppm=64, rib=0.076, streak=8):
    """Corrugated sheeting: ribs every 76 mm running up the slope (u across the ribs), sun and shade
    on each flank, faint weathering streaks down the fall."""
    h, w = int(th * ppm), int(tw * ppm)
    xx = np.arange(w) / ppm
    ph = (xx % rib) / rib
    prof = np.cos(ph * 2 * np.pi) * 0.5 + 0.5
    a = np.zeros((h, w, 3)) + np.array(base, float)
    a += ((prof - 0.5) * 22)[None, :, None]
    st = noise(1, w, 3, streak)[0] + noise(1, w, 11, streak)[0]
    a += st[None, :, None] * np.linspace(0.6, 1.0, h)[:, None, None]
    a += fbm(h, w, 4)[..., None]
    save(name, a, tw, th)


def boards(name, base, board=0.15, tw=2.4, th=2.4, ppm=64, vertical=True, joint=-26, var=5):
    h, w = int(th * ppm), int(tw * ppm)
    a = np.zeros((h, w, 3)) + np.array(base, float)
    n = int(round((tw if vertical else th) / board))
    sh = rng.normal(0, var, n)
    idx = (np.arange(w if vertical else h) / ppm / board).astype(int) % n
    s = sh[idx]
    if vertical:
        a += s[None, :, None]
        j = (np.arange(w) / ppm % board) < 0.012
        a[:, j] += joint
    else:
        a += s[:, None, None]
        j = (np.arange(h) / ppm % board) < 0.012
        a[j] += joint
    a += fbm(h, w, 3)[..., None]
    save(name, a, tw, th)


def concrete(name, base, tw=6.0, th=6.0, ppm=32, joint=3.0, amp=9):
    h, w = int(th * ppm), int(tw * ppm)
    a = np.zeros((h, w, 3)) + np.array(base, float)
    a += fbm(h, w, amp)[..., None]
    a += (rng.random((h, w, 1)) - 0.5) * 8
    if joint:
        k = int(joint * ppm)
        a[::k] -= 30
        a[:, ::k] -= 30
    save(name, a, tw, th)


def glass(name, tw=1.0, th=1.0, ppm=64):
    """A window pane in shade: dark, a sky reflection at the top, a faint frame line."""
    h, w = int(th * ppm), int(tw * ppm)
    t = np.linspace(1, 0, h)[:, None, None]
    a = np.array([28, 34, 40], float) + t * np.array([40, 52, 62], float) + np.zeros((h, w, 3))
    a += fbm(h, w, 3)[..., None]
    save(name, a, tw, th)


def curtain(name, tw=1.5, th=4.5, ppm=64):
    """Curtain-wall glass: a 1.5 m mullion grid with a transom, reflecting a pale sky above and the dark
    room behind below (the mullions themselves are modelled; this is the glass between)."""
    h, w = int(th * ppm), int(tw * ppm)
    t = np.linspace(1, 0, h)[:, None, None]
    a = np.array([46, 62, 74], float) + t * np.array([70, 88, 100], float) + np.zeros((h, w, 3))
    a += noise(h, w, 32, 6)[..., None]
    save(name, a, tw, th)


def stone(name, base, tw=4.0, th=3.0, ppm=64):
    """Random-coursed sandstone: blocks 0.3-0.6 m long in 0.2-0.3 m courses, each its own shade, recessed joints."""
    h, w = int(th * ppm), int(tw * ppm)
    a = np.zeros((h, w, 3)) + np.array(base, float)
    y = 0
    while y < h:
        ch = int(rng.uniform(0.2, 0.32) * ppm)
        x = int(rng.uniform(0, 0.4) * ppm)
        while x < w + ppm:
            cw = int(rng.uniform(0.3, 0.65) * ppm)
            sh = rng.normal(0, 12) + np.array([1.0, 0.9, 0.7]) * rng.normal(0, 5)
            ys, xs = slice(y, min(h, y + ch)), np.arange(x, x + cw) % w
            a[ys][:, xs] += sh
            a[ys][:, xs[:2]] = np.array(base) * 0.62
            x += cw
        a[y:y + 2] = np.array(base) * 0.62
        y += ch
    a += fbm(h, w, 8)[..., None]
    save(name, a, tw, th)


def main():
    brick("brick_red", (150, 72, 54), (176, 160, 140))                  # photo 19: red face brick, pale mortar
    flat("render_cream", (214, 196, 156), amp=4)                         # cream rendered bands and sills
    flat("plinth", (120, 62, 50), amp=5)
    sheeting("roof_red", (150, 66, 56))                                  # Google Earth top: dull Colorbond red
    flat("roof_cap", (132, 58, 50), amp=3)
    flat("flashing", (140, 62, 52), amp=3)
    boards("timber_cream", (226, 210, 168), board=0.14)                  # posts, fascias, gables, cupolas
    flat("fascia_cream", (232, 218, 182), amp=3)
    flat("gable_dark", (52, 44, 38), amp=4)
    boards("timber_dark", (78, 60, 46), board=0.15, vertical=False)
    boards("underside", (108, 98, 86), board=0.6, vertical=False, joint=-18)   # roof underside: sheeting on purlins
    flat("steel_dark", (60, 60, 62), amp=3)
    flat("lead_grey", (92, 98, 96), amp=5)                               # the cupolas' bellcast roofs
    flat("pipe_brown", (92, 54, 40), amp=3)
    concrete("concrete", (168, 164, 156))
    concrete("concrete_riser", (150, 146, 140), joint=0)
    glass("window_dark")
    flat("grass", (92, 128, 62), amp=8)
    flat("paint_white", (236, 236, 232), amp=3)                          # pickets, light towers
    concrete("asphalt", (96, 96, 98), joint=0, amp=7)                     # the walk and the concourse
    flat("alu", (176, 178, 180), amp=3)                                   # bench seats
    flat("lamp_glass", (232, 236, 238), amp=2)
    flat("lamp_body", (120, 124, 128), amp=3)
    # The Wolf Blass Community Centre and the Western Stand (AFLW 2025 photo 23, Google Earth)
    curtain("curtain_glass")
    flat("glass_rail", (120, 140, 150), amp=2)
    flat("steel_charcoal", (52, 54, 58), amp=3)
    flat("render_white", (226, 226, 222), amp=3)
    flat("panel_red", (172, 40, 36), amp=3)
    flat("panel_black", (34, 34, 36), amp=3)
    sheeting("corr_red", (128, 42, 36), tw=1.52, th=4.0)                  # the Western Stand's back (photos 02, 03)
    sheeting("roof_zinc", (178, 180, 178))
    flat("underside_dark", (64, 66, 70), amp=3)
    stone("sandstone", (196, 172, 128))                                  # photos 05-07: rough sandstone blocks
    sheeting("roof_grey", (104, 108, 106))
    sheeting("roof_grey_green", (112, 122, 112))
    sheeting("roof_pale", (186, 186, 180))
    sheeting("corr_cream", (214, 204, 176), th=3.0)
    brick("brick_dark", (132, 64, 50), (150, 136, 120))
    json.dump(SPEC, open(os.path.join(OUT, "spec.json"), "w"), indent=1)
    print(len(SPEC), "textures")


if __name__ == "__main__":
    main()
