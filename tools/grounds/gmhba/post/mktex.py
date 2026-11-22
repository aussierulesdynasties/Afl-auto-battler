"""Hand-drawn textures for the GMHBA post pass (post.py): the north stand's solar panels and the north and east
stands' outside walls, drawn from Google Earth 3D (tools/grounds/gmhba/qa). No photo pixels. 32 px a metre on the
walls (docs/MCG_STANDARD.md).

    python3 tools/grounds/gmhba/post/mktex.py OUTDIR
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PX = 32  # pixels a metre on the walls
rng = np.random.default_rng(5)


def noise(h, w, scale, amp):
    n = rng.random((max(2, h // scale), max(2, w // scale)))
    return (np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), float) / 255 - 0.5) * amp


def finish(a, grain=6):
    a = a + (rng.random(a.shape[:2]) - 0.5)[..., None] * grain
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def solar(out):
    """The north roof's outer plates, v across the plate (0 the leading edge, 1 the back), u 6 m a tile along it.
    Google Earth: bright roof sheeting for the inner 40 % of each plate, then a field of near-black panels in rows,
    a pale strip between rows, a sheeting margin at the back."""
    W, H = 1024, 2048
    base = np.full((H, W, 3), (208, 211, 214), float)
    base += noise(H, W, 64, 14)[..., None]
    # Sheeting ribs every 0.25 m along v (the plate's fall).
    pxm = W / 6.0
    xs = np.arange(W)
    rib = ((xs % int(pxm * 0.25)) < 3)
    base[:, rib] *= 0.9
    a = base
    t0, t1 = 0.40, 0.93
    y0, y1 = int(t0 * H), int(t1 * H)
    # Panels 1.0 m along u, rows of two 1.7 m panels across v, 0.4 m walkway between rows.
    vm = (y1 - y0) / 22.0  # the field is about 22 m deep on the plate
    y = y0
    while y < y1 - 1:
        for k in range(2):
            ya, yb = int(y + k * 1.72 * vm), int(y + (k + 1) * 1.72 * vm) - 1
            if yb > y1:
                break
            for c in range(6):
                xa, xb = int(c * pxm) + 2, int((c + 1) * pxm) - 2
                cell = np.full((yb - ya, xb - xa, 3), (20, 25, 36), float)
                cell += noise(yb - ya, xb - xa, 24, 10)[..., None]
                # A soft sky sheen down the panel.
                cell += np.linspace(10, 0, yb - ya)[:, None, None]
                # Cell grid.
                cell[:, ::int(max(3, (xb - xa) / 6))] += 6
                cell[::int(max(3, (yb - ya) / 10)), :] += 6
                a[ya:yb, xa:xb] = cell
                # Silver frame.
                a[ya:yb, xa:xa + 2] = (110, 114, 120)
                a[ya:yb, xb - 2:xb] = (110, 114, 120)
                a[ya:ya + 2, xa:xb] = (110, 114, 120)
                a[yb - 2:yb, xa:xb] = (110, 114, 120)
        y += (2 * 1.72 + 0.4) * vm
    finish(a, 5).save(os.path.join(out, "solar.png"))


def north(out):
    """The north stands' outside wall, 12 m a tile wide and 25 m tall (v 0 at the top). Google Earth: under the
    roof a dark glazed band behind white V struts (z 16-25), a white band (z 13-16), then white fluted cladding
    to the ground with a dark glazed strip at the concourse (z 3-6)."""
    W, H = 12 * PX, 25 * PX
    a = np.full((H, W, 3), (226, 228, 230), float)
    a += noise(H, W, 32, 10)[..., None]

    def z(m):
        return int(H - m * PX)

    # Fluted cladding, a groove every 0.6 m, z 0-13.
    for x in range(0, W, int(0.6 * PX)):
        a[z(13):, x:x + 2] *= 0.82
        a[z(13):, x + 2:x + 4] *= 1.04
    # Glazed strip at the concourse, mullions every 1.5 m.
    a[z(6):z(3)] = (62, 72, 86)
    a[z(6):z(3)] += np.linspace(30, 0, z(3) - z(6))[:, None, None]
    for x in range(0, W, int(1.5 * PX)):
        a[z(6):z(3), x:x + 3] = (150, 152, 156)
    # Soft grime fading down from under the white band.
    a[z(13):z(10)] *= np.linspace(0.93, 1.0, z(10) - z(13))[:, None, None]
    # The white band.
    a[z(16):z(13)] = (236, 237, 238)
    a[z(13) - 3:z(13)] = (170, 172, 175)
    # Dark glazed band under the roof, with a white V strut pair every 12 m (the roof's fold pitch).
    g0, g1 = z(25), z(16)
    a[g0:g1] = (46, 54, 66)
    a[g0:g1] += np.linspace(0, 26, g1 - g0)[:, None, None]
    for x in range(0, W, int(1.5 * PX)):
        a[g0:g1, x:x + 2] = (90, 96, 104)
    im = finish(a, 5)
    d = ImageDraw.Draw(im)
    for cx in (W * 0.25, W * 0.75):
        d.line([(cx - 4.2 * PX, g0), (cx, g1)], fill=(238, 240, 242), width=int(0.45 * PX))
        d.line([(cx + 4.2 * PX, g0), (cx, g1)], fill=(238, 240, 242), width=int(0.45 * PX))
    im.save(os.path.join(out, "fac_north.png"))


def east(out):
    """The Reg Hickey Stand's outside wall on Moorabool Street, 7.5 m a tile wide and 17 m tall (v 0 at the top).
    Google Earth: pale grey cladding panels with a white pilaster every 7.5 m (each carries a curved white rib above
    the roof), three dark window strips, ground-floor glazing."""
    W, H = int(7.5 * PX), 17 * PX
    a = np.full((H, W, 3), (200, 204, 206), float)
    a += noise(H, W, 32, 12)[..., None]

    def z(m):
        return int(H - m * PX)

    # Panel joints 1.2 m wide, 3.4 m floors.
    for x in range(0, W, int(1.2 * PX)):
        a[:, x:x + 2] *= 0.86
    for m in (3.4, 6.8, 10.2, 13.6):
        a[z(m):z(m) + 2] *= 0.8
    # Window strips.
    for lo, hi in ((0.4, 3.0), (7.4, 8.6), (11.0, 12.2)):
        a[z(hi):z(lo), int(1.4 * PX):int(6.1 * PX)] = (58, 66, 78)
        a[z(hi):z(lo), int(1.4 * PX):int(6.1 * PX)] += np.linspace(28, 0, z(lo) - z(hi))[:, None, None]
        for x in range(int(1.4 * PX), int(6.1 * PX), int(1.2 * PX)):
            a[z(hi):z(lo), x:x + 2] = (140, 144, 150)
    # The white pilaster, shaded on one side.
    pw = int(0.7 * PX)
    a[:, :pw] = (238, 240, 241)
    a[:, pw:pw + 4] = (150, 154, 158)
    # Grime at the foot.
    a[z(0.6):] *= 0.85
    finish(a, 6).save(os.path.join(out, "fac_east.png"))


if __name__ == "__main__":
    o = sys.argv[1]
    os.makedirs(o, exist_ok=True)
    solar(o)
    north(o)
    east(o)
    print("textures in", o)
