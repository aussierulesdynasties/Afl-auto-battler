"""The gum leaf texture: four sprays of eucalypt leaves (2 x 2 atlas, 1024 px), drawn here leaf by leaf.

Each spray is a few drooping twigs carrying narrow lance-shaped leaves, 9 to 14 cm long, hanging edge-on
as gum leaves do, in the dull olive and blue-grey greens of Alice Springs' river red gums and ghost gums,
with gaps between them (the crowns are open). Alpha is 1 on a leaf and 0 between. Nothing is a photo.

    python3 leaves.py OUT.png
"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 1024
H = S // 2
GREENS = [(96, 106, 74), (110, 118, 84), (84, 96, 70), (120, 126, 96), (102, 116, 92), (92, 100, 76)]


def spray(seed):
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (H * 2, H * 2), (0, 0, 0, 0))     # drawn at 2x, then reduced
    d = ImageDraw.Draw(im)
    W = H * 2
    for tw in range(int(rng.integers(13, 18))):
        # a twig from near the top edge or the middle, drooping as it runs out
        x, y = rng.uniform(0.2, 0.8) * W, rng.uniform(0.08, 0.55) * W
        a = rng.uniform(0, 2 * math.pi)
        steps = int(rng.integers(7, 12))
        for k in range(steps):
            nx, ny = x + math.cos(a) * W * 0.045, y + math.sin(a) * W * 0.045 + W * 0.012
            d.line([(x, y), (nx, ny)], fill=(96, 80, 62, 255), width=3)
            for side in (-1, 1):
                if rng.random() < 0.85:
                    _leaf(d, rng, nx, ny, a + side * rng.uniform(0.6, 1.2), W)
            x, y = nx, ny
            a += rng.normal(0, 0.25)
            a = a * 0.9 + (math.pi / 2) * 0.1       # turn toward hanging down
            if not (0 < x < W and 0 < y < W):
                break
    im = im.resize((H, H), Image.LANCZOS)
    a = np.asarray(im).copy()
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    return Image.fromarray(a)


def _leaf(d, rng, x, y, ang, W):
    L = W * rng.uniform(0.085, 0.13)
    w = L * rng.uniform(0.15, 0.22)
    ang = ang * 0.5 + (math.pi / 2) * 0.5 + rng.normal(0, 0.25)   # leaves hang
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for t in np.linspace(0, 1, 9):
        r = w * math.sin(math.pi * t) ** 0.8 * (1 - 0.35 * t)
        pts.append((t * L, r))
    for t in np.linspace(1, 0, 9)[1:-1]:
        r = w * math.sin(math.pi * t) ** 0.8 * (1 - 0.35 * t)
        pts.append((t * L, -r))
    bend = rng.uniform(-0.25, 0.25)
    out = [(x + ca * u - sa * (v + bend * u * u / L), y + sa * u + ca * (v + bend * u * u / L)) for u, v in pts]
    g = np.array(GREENS[int(rng.integers(len(GREENS)))], float) * rng.uniform(0.85, 1.12)
    d.polygon(out, fill=tuple(int(c) for c in np.clip(g, 0, 255)) + (255,))
    # the midrib, a shade lighter
    d.line([(x, y), (x + ca * L * 0.9, y + sa * L * 0.9)], fill=tuple(int(min(255, c * 1.18)) for c in g) + (255,), width=1)


def main(out):
    atlas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for k in range(4):
        atlas.paste(spray(11 + k), ((k % 2) * H, (k // 2) * H))
    # colour under the transparent texels: the mean leaf green, so mipmaps do not darken to black at the edges
    a = np.asarray(atlas).astype(np.float32)
    m = a[..., 3] > 0
    # gum leaves read a grey-green: Google Earth's sunlit canopies over Alice Springs measure about 76, 93, 90
    # (canopy_mask core, brightest 40%), in its cool cast; the sprays take that hue, a little lighter (the game
    # lights them, Google Earth's include the crown's own shade)
    a[..., :3] *= np.array([104.0, 120.0, 106.0]) / a[m][:, :3].mean(0)
    a = np.clip(a, 0, 255).astype(np.uint8)
    mean = a[m][:, :3].mean(0)
    a[~m, :3] = mean
    Image.fromarray(a).save(out)
    print("leaves", out, "cover %.2f" % m.mean())


if __name__ == "__main__":
    main(sys.argv[1])
