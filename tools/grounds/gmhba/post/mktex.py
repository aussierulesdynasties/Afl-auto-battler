"""Hand-drawn textures for the GMHBA post pass (post.py): the north stand's solar panels and the north and east
stands' outside walls, drawn from Google Earth 3D (tools/grounds/gmhba/qa). No photo pixels. 32 px a metre on the
walls (docs/MCG_STANDARD.md).

    python3 tools/grounds/gmhba/post/mktex.py OUTDIR
"""
import os
import sys

import numpy as np
from PIL import Image

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
    # The white V struts in front of this band are modelled (post.py), not painted.
    im = finish(a, 5)
    im.save(os.path.join(out, "fac_north.png"))


def east(out):
    """The Reg Hickey Stand's outside wall on Moorabool Street, one bay (13 m) a tile wide and 17 m tall (v 0 at the top).
    Google Earth: pale grey cladding panels with three dark window strips (the white pilasters
    under the roof's ribs are modelled in post.py), ground-floor glazing."""
    W, H = 13 * PX, 17 * PX   # one bay between two roof ribs (about 13 m; post.py maps each bay to one tile)
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
        a[z(hi):z(lo), int(1.3 * PX):int(11.7 * PX)] = (58, 66, 78)
        a[z(hi):z(lo), int(1.3 * PX):int(11.7 * PX)] += np.linspace(28, 0, z(lo) - z(hi))[:, None, None]
        for x in range(int(1.3 * PX), int(11.7 * PX), int(1.2 * PX)):
            a[z(hi):z(lo), x:x + 2] = (140, 144, 150)
    # The white pilasters are modelled (post.py), lined up with the roof's curved ribs.
    # Grime at the foot.
    a[z(0.6):] *= 0.85
    finish(a, 6).save(os.path.join(out, "fac_east.png"))


def glb_image(name):
    """An image of the source model (tools/grounds/gmhba/gmhba.glb) by name, as RGB floats."""
    import io
    import pygltflib
    g = pygltflib.GLTF2().load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gmhba.glb"))
    blob = g.binary_blob()
    for im in g.images:
        if im.name == name:
            bv = g.bufferViews[im.bufferView]
            data = blob[bv.byteOffset:bv.byteOffset + bv.byteLength]
            return np.asarray(Image.open(io.BytesIO(data)).convert("RGB"), float)
    raise KeyError(name)


def unpainted(out):
    """The source textures that painted geometry on (docs/MCG_STANDARD.md: none of that). post.py models
    the geometry; here the painting comes off and the surface behind it stays.
    - slats (Players Stand's south-west face): the white slats over the top 71 % go; the navy backing and the
      dark window slots stay.
    - recess (under the west upper tier): the rake beams every 4.5 m (columns 0-63 and 512-568) go.
    - fins: the painted fins go (modelled); screen: the red casing goes (modelled); lamp heads: the painted
      grid of lamps goes (each lamp modelled)."""
    a = glb_image("slats")
    top = int(a.shape[0] * 0.71) + 3
    band = a[:top]
    lum = band.mean(2)
    navy = np.array([36.0, 46.0, 72.0])
    slot = lum < 60
    band[:] = navy + noise(top, a.shape[1], 16, 6)[..., None]
    band[slot] = (26, 30, 40)
    finish(a, 3).save(os.path.join(out, "slats_backing.png"))
    r = glb_image("recess")
    for x0, x1 in ((0, 64), (512, 569)):
        w = x1 - x0
        src = r[:, x1:x1 + w] if x1 + w <= r.shape[1] else r[:, x0 - w:x0]
        r[:, x0:x1] = src
    finish(r, 2).save(os.path.join(out, "recess_plain.png"))
    # fins (the screen on the west side's south end): grey fins 0.22 m wide every 0.48 m over dark openings.
    # The fins are modelled; the backing is the openings' dark.
    f = glb_image("fins")
    f[:] = np.array([26.0, 27.0, 30.0]) + noise(f.shape[0], f.shape[1], 16, 4)[..., None]
    finish(f, 2).save(os.path.join(out, "fins_backing.png"))
    # The scoreboard: the red casing round the screen is modelled; the screen keeps its dark LED grid.
    sc = glb_image("screen")
    red = (sc[..., 0] > 150) & (sc[..., 1] < 80)
    sc[red] = sc[192, 362]
    finish(sc, 1).save(os.path.join(out, "screen_plain.png"))

    # The Premiership Stand's Cats wall: Google Earth shows silver-grey metal cladding (about 0.7 of the white
    # roof's brightness, neutral), not cream. The cream goes to that grey; the logo, the band and the glazing stay.
    b = glb_image("beige")
    lum = b.mean(2)
    cream = (lum > 170) & (b[..., 0] - b[..., 2] > 10)
    g = lum[cream][:, None] * 0.74 * np.array([[0.98, 1.0, 1.03]])
    b[cream] = g
    # The Cats emblem: the source's was a crude drawing (a square-eared cat, a star for a nose, CATS in a
    # rounded face). Erase it with the cladding of the same columns (the ribs run up the wall), then put on the
    # emblem traced from Google Earth (trace_emblem.py) where Google Earth has it: 0.17 of the wall's width,
    # centred 0.31 across, its middle 0.57 down the cladding (above the navy band at row 364). Drawn at 2x.
    b[150:352, 200:400] = np.tile(b[4:105, 200:400], (2, 1, 1))
    b = np.asarray(Image.fromarray(np.clip(b, 0, 255).astype(np.uint8)).resize((b.shape[1] * 2, b.shape[0] * 2),
                                                                                 Image.BICUBIC), float)
    em = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex_src_cats_emblem.png"))
    w = int(0.17 * b.shape[1])
    em = em.resize((w, round(w * em.height / em.width)), Image.LANCZOS)
    x0, y0 = int(0.31 * b.shape[1] - w / 2), int(0.57 * 728 - em.height / 2)
    wall = Image.fromarray(np.clip(b, 0, 255).astype(np.uint8)).convert("RGBA")
    wall.alpha_composite(em, (x0, y0))
    b = np.asarray(wall.convert("RGB"), float)
    finish(b, 2).save(os.path.join(out, "beige_grey.png"))

    def plain(name, rgb, size=64, amp=6):
        a = np.full((size, size, 3), rgb, float) + noise(size, size, 8, amp)[..., None]
        finish(a, 2).save(os.path.join(out, name))
    plain("fin_grey.png", (150, 154, 160))
    plain("frame_red.png", (196, 30, 36))
    plain("lamphead.png", (78, 82, 88))
    # The lamps' glass by day (Google Earth): dark reflective glass over a silver reflector, brighter in the middle.
    yy, xx = np.mgrid[0:64, 0:64]
    g = 70 + 70 * np.exp(-((yy - 32) ** 2 + (xx - 32) ** 2) / 200.0)
    finish(np.repeat(g[..., None], 3, 2) - np.array([6.0, 3.0, 0.0]), 1).save(os.path.join(out, "lamp_glass.png"))


if __name__ == "__main__":
    o = sys.argv[1]
    os.makedirs(o, exist_ok=True)
    solar(o)
    north(o)
    east(o)
    unpainted(o)
    print("textures in", o)
