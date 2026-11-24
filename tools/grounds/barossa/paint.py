"""Barossa Park's textures, painted in code (no photo pixels). Each returns (image, metres across, metres down) so the
model's metre UVs tile it at true scale. Colours are sampled by eye from the reference photos in the README and kept
as sRGB here; glTF base colour textures are sRGB.

Textures carry only detail too small to model: stone coursing, sheet ribs, paint wear. Every opening, pier, reveal,
column, rail and step is modelled in build.py.
"""
import numpy as np

RNG = np.random.default_rng(7)


def noise(h, w, cells, seed=0):
    """smooth value noise in 0..1, tiling"""
    r = np.random.default_rng(seed)
    g = r.random((cells, cells))
    ys = np.arange(h) / h * cells
    xs = np.arange(w) / w * cells
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    y1 = (y0 + 1) % cells
    x1 = (x0 + 1) % cells
    a = g[y0][:, x0] * (1 - fx) + g[y0][:, x1] * fx
    b = g[y1][:, x0] * (1 - fx) + g[y1][:, x1] * fx
    return a * (1 - fy) + b * fy


def fbm(h, w, seed=0, octaves=(4, 8, 16, 32), amps=(0.5, 0.25, 0.15, 0.1)):
    out = np.zeros((h, w))
    for k, (c, a) in enumerate(zip(octaves, amps)):
        out += noise(h, w, c, seed + k) * a
    return out / sum(amps)


def img(arr):
    return np.clip(arr, 0, 255).astype(np.uint8)


def flat(col, size=64, var=6, seed=1, metres=4.0):
    n = fbm(size, size, seed)
    a = np.ones((size, size, 3)) * np.array(col, float)
    a += (n[..., None] - 0.5) * var * 2
    return img(a), metres, metres


def sandstone():
    """Barossa sandstone ashlar, random coursed: honey, buff and grey-pink blocks of 0.25-0.5 m courses, 1 cm joints.
    4 m x 2 m tile at 128 px/m."""
    W, H, ppm = 512, 256, 128
    a = np.zeros((H, W, 3))
    base = [(206, 178, 136), (192, 160, 118), (214, 192, 152), (178, 150, 116), (200, 170, 140), (186, 166, 136)]
    y = 0
    r = np.random.default_rng(11)
    while y < H:
        ch = int(ppm * r.choice([0.25, 0.3, 0.4, 0.5]))
        ch = min(ch, H - y)
        x = int(r.integers(0, ppm // 2))
        xs = [0]
        while x < W:
            xs.append(x)
            x += int(ppm * r.uniform(0.45, 1.2))
        xs.append(W)
        for x0, x1 in zip(xs[:-1], xs[1:]):
            c = np.array(base[r.integers(len(base))], float) * r.uniform(0.92, 1.06)
            a[y:y + ch, x0:x1] = c
            a[y:y + ch, x0:x0 + 1] = (150, 140, 124)
        a[y:y + 1, :] = (150, 140, 124)
        y += ch
    n = fbm(H, W, 3, (8, 16, 64, 128))
    a *= (0.9 + 0.2 * n)[..., None]
    return img(a), W / ppm, H / ppm


def cladding(col=(58, 60, 63), rib=0.3, size=256, metres=2.4):
    """steel cladding, vertical ribs every `rib` m"""
    a = np.ones((size, size, 3)) * np.array(col, float)
    xs = (np.arange(size) / size * metres) % rib
    edge = (xs < 0.025) | (np.abs(xs - rib / 2) < 0.01)
    a[:, edge] *= 0.82
    a *= (0.95 + 0.1 * fbm(size, size, 5))[..., None]
    return img(a), metres, metres


def roof_sheet(col=(232, 232, 228), rib=0.2, size=256, metres=2.0):
    """Colorbond trimdek-style sheet, light (Surfmist); ribs along v"""
    a = np.ones((size, size, 3)) * np.array(col, float)
    xs = (np.arange(size) / size * metres) % rib
    a[:, xs < 0.03] *= 0.88
    a[:, (xs >= 0.03) & (xs < 0.045)] *= 1.04
    a *= (0.96 + 0.08 * fbm(size, size, 9))[..., None]
    return img(a), metres, metres


def concrete(col=(196, 192, 184), size=256, metres=6.0, joints=3.0, seed=4):
    a = np.ones((size, size, 3)) * np.array(col, float)
    a *= (0.92 + 0.14 * fbm(size, size, seed, (4, 16, 64, 128)))[..., None]
    if joints:
        g = (np.arange(size) / size * metres) % joints
        a[:, g < 0.02] *= 0.8
        a[g < 0.02, :] *= 0.8
    return img(a), metres, metres


def asphalt(size=256, metres=8.0):
    a = np.ones((size, size, 3)) * np.array((74, 74, 76), float)
    n = fbm(size, size, 21, (8, 32, 128, 256), (0.3, 0.3, 0.2, 0.2))
    a *= (0.85 + 0.3 * n)[..., None]
    return img(a), metres, metres


def grass(col=(98, 124, 62), size=256, metres=12.0, seed=31):
    a = np.ones((size, size, 3)) * np.array(col, float)
    n = fbm(size, size, seed, (4, 12, 48, 160))
    a *= (0.82 + 0.36 * n)[..., None]
    return img(a), metres, metres


def dry_grass(size=256, metres=16.0):
    return grass((168, 150, 102), size, metres, 33)


def mulch(size=256, metres=6.0):
    a = np.ones((size, size, 3)) * np.array((112, 86, 62), float)
    a *= (0.75 + 0.5 * fbm(size, size, 41, (16, 64, 128, 256)))[..., None]
    return img(a), metres, metres


def court(col, lines=False, size=64, metres=8.0):
    return flat(col, size, 3, 51, metres)


def seat_deck(size=128, metres=1.6):
    """aluminium seating plank tread, ribbed across"""
    a = np.ones((size, size, 3)) * np.array((176, 178, 178), float)
    ys = (np.arange(size) / size * metres) % 0.1
    a[ys < 0.012, :] *= 0.8
    return img(a), metres, metres


def roller_door(col=(60, 62, 64), size=128, metres=2.0):
    a = np.ones((size, size, 3)) * np.array(col, float)
    ys = (np.arange(size) / size * metres) % 0.08
    a[ys < 0.012, :] *= 0.75
    a[(ys >= 0.012) & (ys < 0.02), :] *= 1.15
    return img(a), metres, metres


def ballast(size=256, metres=6.0):
    a = np.ones((size, size, 3)) * np.array((122, 108, 92), float)
    a *= (0.7 + 0.6 * fbm(size, size, 61, (32, 64, 128, 256), (0.1, 0.2, 0.3, 0.4)))[..., None]
    return img(a), metres, metres


def screen_face(size=64, metres=2.0):
    a = np.ones((size, size, 3)) * np.array((22, 24, 28), float)
    g = (np.arange(size) / size * metres) % 0.5
    a[:, g < 0.01] = 40
    a[g < 0.01, :] = 40
    return img(a), metres, metres
