"""Hand-painted facade atlas: every building gets its own cell (own wall colour, own window layout, own glass).
Usage: python tex_facade_atlas.py <name>   (reads data/<name>/prep/buildings.json, spec/<name>.json)
Writes data/<name>/prep/atlas_<cls>.png (RGBA: alpha 255 = glass, 0 = painted wall) and atlas_cells.json.
Cell u spans the building's whole perimeter, v spans base -> top, so nothing repeats inside a building."""
import json, math, os, sys
import numpy as np
from PIL import Image

name = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, 'data', name, 'prep')
spec = json.load(open(os.path.join(HERE, 'spec', name + '.json')))
PAL = spec['palette']
BL = json.load(open(os.path.join(D, 'buildings.json')))
rng = np.random.default_rng(spec.get('seed', 1) + 77)

# cell size (px) and atlas size per class
CFG = {'house': (128, 48, 4096), 'block': (256, 64, 4096), 'tower': (1024, 512, 4096)}
PAD = 3


def jitter(c, amt):
    c = np.array(c, float) * (1 + amt * (rng.random() - 0.5)) + rng.normal(0, amt * 40, 3)
    return np.clip(c, 0, 255)


def paint(cls, b, W, H):
    """returns HxWx4 uint8; wall painted in its own colour, glass alpha 255."""
    walls = PAL['walls_' + cls]
    wc = jitter(walls[b['wall'] % len(walls)], 0.18)
    img = np.zeros((H, W, 4), float); img[..., :3] = wc
    # plaster/brick grain: low-frequency blotches + fine noise (hand-painted look, not photo)
    yy, xx = np.mgrid[0:H, 0:W]
    ph = rng.random(4) * 6.28
    blot = (np.sin(xx / W * 6.28 * (1 + rng.integers(3)) + ph[0]) * np.sin(yy / H * 6.28 + ph[1])) * 6
    img[..., :3] += blot[..., None] + rng.normal(0, 3.0, (H, W, 1))
    # grime toward the base, lighter parapet band at the top
    img[..., :3] *= (1.0 - 0.12 * (yy / H))[..., None]   # grime toward the base
    h = max(3.0, b['h'])
    per = b['per']
    floors = max(1, int(round(h / (3.0 if cls == 'house' else 3.4))))
    bay = {'house': 3.6, 'block': 4.2, 'tower': 3.0}[cls] * (0.85 + 0.3 * rng.random())
    cols = max(2, int(round(per / bay)))
    style = rng.choice({'house': ['punched', 'punched', 'wide'],
                        'block': ['punched', 'ribbon', 'balcony', 'shed', 'punched'],
                        'tower': ['curtain', 'ribbon', 'balcony', 'punched']}[cls])
    if cls == 'block' and h <= 6: style = rng.choice(['shed', 'punched', 'shed'])
    gbase = np.array([[70, 92, 112], [58, 74, 86], [96, 120, 132], [52, 66, 72], [88, 104, 118], [74, 84, 70]][rng.integers(6)], float)
    gbase = jitter(gbase, 0.2)
    fh = H / floors                                      # px per floor
    top_m = H - 1 - int(0.6 / h * H) if cls != 'house' else H  # parapet
    cw = W / cols
    if cls != 'house':
        img[: max(1, int(0.7 / h * H)), :, :3] = np.clip(wc * 1.12 + 8, 0, 255)   # parapet cap (row 0 = top)
    def glass(y0, y1, x0, x1):
        y0, y1, x0, x1 = max(0, int(round(y0))), min(H, int(round(y1))), max(0, int(round(x0))), min(W, int(round(x1)))
        if y1 <= y0 or x1 <= x0: return
        g = jitter(gbase, 0.12)
        hh = y1 - y0
        grad = np.linspace(1.18, 0.82, hh)[:, None, None] if rng.random() < 0.7 else np.linspace(0.85, 1.12, hh)[:, None, None]
        sky = rng.random() < 0.25
        col = g * grad + (np.array([40, 46, 50]) if sky else 0)
        img[y0:y1, x0:x1, :3] = np.clip(col + rng.normal(0, 2, (hh, x1 - x0, 1)), 0, 255)
        img[y0:y1, x0:x1, 3] = 255
        if rng.random() < 0.3 and x1 - x0 > 2:     # drawn blind / curtain in some windows
            yb = y0 + int(hh * rng.uniform(0.2, 0.6))
            img[y0:yb, x0:x1, :3] = jitter([200, 196, 180], 0.15); img[y0:yb, x0:x1, 3] = 254
    for f in range(floors):
        yb = H - f * fh                # floor bottom (px, rows count down from top)
        yt = yb - fh
        if style == 'curtain':
            glass(yt + 1, yb - 1, 0, W)
            for c in range(cols + 1):      # mullions in wall colour
                x = int(c * cw); img[int(yt):int(yb), x:x + 1, :3] = wc * 0.9; img[int(yt):int(yb), x:x + 1, 3] = 0
            img[int(yb) - 1:int(yb), :, :3] = wc * 0.8; img[int(yb) - 1:int(yb), :, 3] = 0
        elif style == 'ribbon':
            glass(yt + fh * 0.32, yb - fh * 0.12, 0, W)
            for c in range(cols):
                x = int(c * cw); img[int(yt):int(yb), x:x + 1, 3] = 0; img[int(yt):int(yb), x:x + 1, :3] = wc * 0.85
        elif style == 'shed':
            if f == 0:
                for c in range(cols):
                    r = rng.random()
                    if r < 0.12:   # roller door
                        x0 = c * cw + cw * 0.15; x1 = c * cw + cw * 0.85
                        img[int(yt + fh * 0.2):int(yb), int(x0):int(x1), :3] = jitter([150, 152, 150], 0.2)
                    elif r < 0.35:
                        glass(yt + fh * 0.35, yt + fh * 0.7, c * cw + cw * 0.2, c * cw + cw * 0.8)
            # cladding ribs
            for x in range(0, W, max(2, int(cw / 4))):
                img[int(yt):int(yb), x, :3] *= 0.92
        else:  # punched / wide / balcony
            for c in range(cols):
                if cls == 'house' and f == 0 and c % max(3, cols // 2) == 1:   # door
                    img[int(yt + fh * 0.2):int(yb), int(c * cw + cw * 0.35):int(c * cw + cw * 0.65), :3] = jitter([92, 66, 48], 0.3)
                    continue
                if rng.random() < (0.12 if cls == 'house' else 0.05): continue
                wf = 0.75 if style == 'wide' else 0.5
                glass(yt + fh * 0.25, yb - fh * 0.2, c * cw + cw * (1 - wf) / 2, c * cw + cw * (1 + wf) / 2)
            if style == 'balcony' and f > 0:
                yr = int(yb - fh * 0.32)
                img[yr:int(yb), :, :3] = np.clip(wc * 1.15 + 10, 0, 255); img[yr:int(yb), :, 3] = 0
                img[yr:yr + 1, :, :3] = wc * 0.6
    # slab line at grade, darker plinth
    img[H - max(1, int(0.8 / h * H)):, :, :3] *= 0.82
    img[H - max(1, int(0.8 / h * H)):, :, 3] = 0
    return np.clip(img, 0, 255).astype(np.uint8)


for b in BL:
    P = np.array(b['p'], float)
    b['per'] = float(np.hypot(*np.diff(np.vstack([P, P[:1]]), axis=0).T).sum())
cells = {}
for cls, (CW, CH, S) in CFG.items():
    idx = [i for i, b in enumerate(BL) if b['c'] == cls]
    if not idx: continue
    nx, ny = S // CW, S // CH
    assert len(idx) <= nx * ny, (cls, len(idx), nx * ny)
    A = np.zeros((S, S, 4), np.uint8)
    for k, i in enumerate(idx):
        cx, cy = k % nx, k // nx
        x0, y0 = cx * CW, cy * CH
        w, h = CW - 2 * PAD, CH - 2 * PAD
        A[y0 + PAD:y0 + PAD + h, x0 + PAD:x0 + PAD + w] = paint(cls, BL[i], w, h)
        # bleed edges into padding
        A[y0:y0 + PAD, x0 + PAD:x0 + PAD + w] = A[y0 + PAD, x0 + PAD:x0 + PAD + w]
        A[y0 + PAD + h:y0 + CH, x0 + PAD:x0 + PAD + w] = A[y0 + PAD + h - 1, x0 + PAD:x0 + PAD + w]
        A[y0:y0 + CH, x0:x0 + PAD] = A[y0:y0 + CH, x0 + PAD:x0 + PAD + 1]
        A[y0:y0 + CH, x0 + PAD + w:x0 + CW] = A[y0:y0 + CH, x0 + PAD + w - 1:x0 + PAD + w]
        # uv rect (u0, v0 bottom, u1, v1 top) in glTF/Blender convention (v up)
        cells[i] = [(x0 + PAD + 0.5) / S, 1 - (y0 + PAD + h - 0.5) / S, (x0 + PAD + w - 0.5) / S, 1 - (y0 + PAD + 0.5) / S]
    Image.fromarray(A, 'RGBA').save(os.path.join(D, 'atlas_%s.png' % cls), optimize=True)
    print(cls, len(idx), 'cells')
json.dump(cells, open(os.path.join(D, 'atlas_cells.json'), 'w'))
