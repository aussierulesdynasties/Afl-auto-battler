"""The 3D oval's turf textures (row 197), made here so they are ours (no licence to track).

    python tools/oval3d/make_turf_textures.py [SEED]

Writes to assets/oval3d/turf/:
  blades.png         1024 x 1024 tile of mown couch/rye turf seen from above, 0.6 m across:
                     about 30,000 blades 2-3 mm wide, each darker at its base and lighter at its
                     tip, leaning along +v (the mower's direction; the shader turns it per stripe).
                     Stored as variation about the turf's colour: RGB = colour / mean * 0.5, so
                     the shader multiplies the day's grass colour by 2 * texel.
  blades_n.png       its normal map (each blade a ridge rising to its tip), tangent space.
  patches.png        512 x 512 tile of smooth noise: R broad patches, G clumps, B fine mottle.
Every image tiles seamlessly (blades wrap at the edges; noise is blurred with wrap-around).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "oval3d", "turf")
N = 1024
TILE_M = 0.6
PX_MM = TILE_M * 1000.0 / N   # mm a pixel (about 0.59)


def blades(rng):
    # Thatch under the blades: dark, brownish green.
    col = Image.new("RGB", (N, N), (22, 38, 14))
    hgt = Image.new("L", (N, N), 0)
    dc = ImageDraw.Draw(col)
    dh = ImageDraw.Draw(hgt)
    count = 30000
    for _ in range(count):
        x = rng.uniform(0, N)
        y = rng.uniform(0, N)
        length = rng.uniform(9.0, 30.0) / PX_MM * 0.6      # 9-30 mm of blade, foreshortened
        width = max(2, int(round(rng.uniform(2.0, 3.4) / PX_MM)))
        ang = math.radians(90.0 + rng.normal(0.0, 22.0))    # leaning along +v, spread
        dx = math.cos(ang) * length
        dy = math.sin(ang) * length
        # The blade's own green: most a healthy mid green, some yellower, some bluer, a few dead.
        r = rng.random()
        if r < 0.06:
            base = np.array([96, 92, 46])      # dead / dry
        elif r < 0.3:
            base = np.array([70, 120, 38])     # yellow-green
        elif r < 0.55:
            base = np.array([40, 98, 44])      # blue-green
        else:
            base = np.array([52, 112, 40])
        base = base * rng.uniform(0.8, 1.15)
        segs = 5
        for s in range(segs):
            t0 = s / segs
            t1 = (s + 1) / segs
            # Darker at the base (shaded by its neighbours), lighter toward the tip.
            shade = 0.55 + 0.6 * t1
            c = tuple(int(min(255, v * shade)) for v in base)
            h = int(60 + 190 * t1)
            w = max(1, int(round(width * (1.0 - 0.55 * t0))))
            for ox in (-N, 0, N):
                for oy in (-N, 0, N):
                    ax = x + dx * t0 + ox
                    ay = y + dy * t0 + oy
                    bx = x + dx * t1 + ox
                    by = y + dy * t1 + oy
                    if max(ax, bx) < -40 or min(ax, bx) > N + 40 or max(ay, by) < -40 or min(ay, by) > N + 40:
                        continue
                    dc.line([(ax, ay), (bx, by)], fill=c, width=w)
                    dh.line([(ax, ay), (bx, by)], fill=h, width=w)
    a = np.asarray(col).astype(np.float64)
    mean = a.reshape(-1, 3).mean(axis=0)
    var = np.clip(a / mean * 0.5, 0.0, 1.0)
    Image.fromarray((var * 255.0 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "blades.png"))
    # Normal map from the height (wrap-around differences, so it tiles).
    hh = np.asarray(hgt.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float64) / 255.0
    strength = 3.0
    gx = (np.roll(hh, -1, axis=1) - np.roll(hh, 1, axis=1)) * 0.5 * strength
    gy = (np.roll(hh, -1, axis=0) - np.roll(hh, 1, axis=0)) * 0.5 * strength
    n = np.stack([-gx, gy, np.ones_like(hh)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255.0 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "blades_n.png"))
    return mean


def smooth_noise(rng, size, sigma):
    """Tileable noise: white noise blurred by a Gaussian in the frequency domain (wraps)."""
    w = rng.standard_normal((size, size))
    f = np.fft.fftfreq(size)
    k2 = f[None, :] ** 2 + f[:, None] ** 2
    g = np.exp(-2.0 * (math.pi ** 2) * (sigma ** 2) * k2)
    out = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    out = (out - out.mean()) / (out.std() + 1e-9)
    return np.clip(0.5 + out * 0.18, 0.0, 1.0)


def patches(rng):
    s = 512
    r = smooth_noise(rng, s, 40.0)
    g = smooth_noise(rng, s, 9.0)
    b = smooth_noise(rng, s, 2.5)
    img = np.stack([r, g, b], axis=-1)
    Image.fromarray((img * 255.0 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "patches.png"))


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261115
    rng = np.random.default_rng(seed)
    os.makedirs(OUT, exist_ok=True)
    mean = blades(rng)
    patches(rng)
    print("wrote", OUT, "blade mean colour", mean.round(1))


if __name__ == "__main__":
    main()
