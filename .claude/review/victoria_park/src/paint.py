# paint.py: hand-made textures for Victoria Park (no photo pixels). Each texture is drawn at real scale; TILE gives the
# metres (or units) one copy covers, build.py maps UVs (metres) through it. Colours read from the reference (colsample.py).
import numpy as np, json, os
from PIL import Image
os.makedirs('tex3', exist_ok=True)
rng = np.random.default_rng(11)
PPM = 256                      # pixels per metre (sharp at a 2 m close-up)
TILE = {}

def noise(h, w, cell, amp, seed=0):
    # tileable value noise: random grid, bicubic upsampling with wrap
    r = np.random.default_rng(seed)
    gh, gw = max(1, h // cell), max(1, w // cell)
    g = r.standard_normal((gh, gw))
    im = Image.fromarray(((g - g.min()) / (np.ptp(g) + 1e-9) * 255).astype(np.uint8))
    big = np.array(im.resize((gw * cell + 3 * cell, gh * cell + 3 * cell), Image.BICUBIC)).astype(float)
    big = np.tile(np.array(im).astype(float), (3, 3))
    big = np.array(Image.fromarray(big.astype(np.uint8)).resize((gw * 3 * cell, gh * 3 * cell), Image.BICUBIC)).astype(float)
    out = big[gh * cell:gh * cell + h, gw * cell:gw * cell + w]
    return (out / 255 - 0.5) * 2 * amp

def grain(h, w, amp, seed=1):
    return np.random.default_rng(seed).standard_normal((h, w)) * amp

def save(name, img, tile):
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save('tex3/%s.png' % name); TILE[name] = tile

def solid(h, w, col):
    return np.ones((h, w, 3)) * np.array(col, float)

def corrugated(col, wm, hm, rib=0.076, along_v=True, depth=0.22, seed=0, lap=None):
    # ribs run along v (vary with u): sine shading, one rib = `rib` m
    w, h = int(wm * PPM), int(hm * PPM)
    x = np.arange(w) / PPM
    sh = 1 + depth * np.sin(2 * np.pi * x / rib)                 # lit flank / shaded flank
    img = solid(h, w, col) * sh[None, :, None]
    img += noise(h, w, 64, 6, seed)[..., None] + grain(h, w, 2.0, seed)[..., None]
    if lap:                                                       # sheet side-laps (darker line)
        for k in range(int(wm / lap)):
            c = int(k * lap * PPM); img[:, c:c + 2] *= 0.85
    return img

# ---- roofs: corrugated sheet, 76 mm ribs, 762 mm sheet cover (30 ribs per 2.286 m tile) ----
for nm, col in (('roof', (198, 195, 189)), ('roof_ry', (186, 195, 196)), ('under', (176, 174, 170))):
    save(nm, corrugated(col, 2.286, 2.286, lap=0.762, seed=len(nm)), (2.286, 2.286))

# ---- Sherrin rear cladding: corrugated metal painted in black and white stripes (CMP 2003), pair = 1.66 m ----
wm, hm = 3.32, 3.32; w, h = int(wm * PPM), int(hm * PPM)
x = np.arange(w) / PPM
white = ((x % 1.66) < 0.83)
base = np.where(white[:, None], np.array([236, 236, 233.]), np.array([28, 28, 30.]))   # (w,3)
img = np.repeat(base[None], h, 0)
img *= (1 + 0.16 * np.sin(2 * np.pi * x / (0.83 / 11)))[None, :, None]
img += noise(h, w, 80, 5, 3)[..., None] + grain(h, w, 1.5, 3)[..., None]
save('cladding', img, (3.32, 3.32))

# ---- Lulie St boundary wall: one bay = exposed-aggregate panel between smooth concrete piers, coping on top ----
# v runs top (0) to ground (4 m); u in bays
w, h = 1500, 1024          # one bay (5.85 m) x 4 m
img = solid(h, w, (178, 170, 156))
agg = rng.random((h, w))
stones = np.array(Image.fromarray((agg * 255).astype(np.uint8)).filter(__import__('PIL.ImageFilter', fromlist=['x']).MinFilter(3))) / 255.0
pebble = (stones > 0.35)
panel = np.ones((h, w), bool)
pier_w = int(w * 0.75 / 5.85)              # 0.75 m pier
panel[:, :pier_w] = False; panel[:int(h * 0.3 / 4)] = False   # coping 0.3 m
pcol = np.where(pebble[..., None], np.array([150, 140, 126.]), np.array([96, 90, 82.]))
pcol += grain(h, w, 14, 5)[..., None]
img[panel] = pcol[panel]
pier = ~panel
img[pier] = (np.array([200, 194, 182.]) + grain(h, w, 4, 6)[..., None] + noise(h, w, 60, 5, 6)[..., None])[pier]
# panel border recess and coping shadow
img[int(h * 0.3 / 4):int(h * 0.3 / 4) + 6] *= 0.7
img[:, pier_w:pier_w + 5] *= 0.7; img[:, w - 4:] *= 0.85
save('aggr', img, (1.0, 4.0))

# ---- brick: 230x76 mm face + 10 mm mortar, stretcher bond; 10 x 10 courses ----
bw, bh = 0.240, 0.086; wm, hm = bw * 10, bh * 20; w, h = int(wm * PPM), int(hm * PPM)
img = solid(h, w, (210, 205, 196))     # mortar
for r in range(20):
    y0 = int(r * bh * PPM); y1 = int((r * bh + 0.076) * PPM)
    off = 0 if r % 2 == 0 else bw / 2
    for c in range(-1, 11):
        x0 = int((c * bw + off) * PPM); x1 = int((c * bw + off + 0.230) * PPM)
        col = np.array([168, 96, 76.]) * (0.88 + 0.24 * rng.random())
        xa, xb = max(0, x0), min(w, x1)
        if xb > xa: img[y0:y1, xa:xb] = col
img += grain(h, w, 5, 9)[..., None]
save('brick', img, (wm, hm))

# ---- concrete (plats, terraces, risers, walks, concourse): board-formed, joints every 2 m ----
def concrete(col, wm, hm, seed, joint=None, big=9):
    w, h = int(wm * PPM), int(hm * PPM)
    img = solid(h, w, col) + noise(h, w, 128, big, seed)[..., None] + noise(h, w, 16, 3, seed + 1)[..., None] + grain(h, w, 3, seed)[..., None]
    if joint:
        for k in range(int(wm / joint)): c = int(k * joint * PPM); img[:, c:c + 3] *= 0.8
    return img
save('plat', concrete((188, 182, 178), 4.0, 0.8, 20, joint=2.0), (4.0, 1.0))      # v = one tread
# terrace tread: worn pale nosing on the front edge (image bottom = v 0), dark drain line at the back
img = concrete((186, 178, 176), 4.0, 0.8, 21, joint=2.0); E = int(0.05 * PPM)
img[-E:] = img[-E:] * 0.25 + np.array((228, 222, 216)) * 0.75; img[:int(0.03 * PPM)] *= 0.72
save('terr', img, (4.0, 1.0))
save('riser', concrete((146, 140, 136), 4.0, 0.4, 22, joint=2.0), (4.0, 1.0))
# aisle half-steps: lighter concrete, white painted nosing on each step edge
img = concrete((204, 198, 194), 1.2, 0.4, 25, big=2); img[-int(0.06 * PPM):] = (238, 236, 232)
save('aisle', img, (1.2, 1.0))
save('concrete', concrete((196, 186, 184), 4.0, 4.0, 23, joint=2.0), (4.0, 4.0))
save('asphalt', concrete((180, 174, 172), 4.0, 4.0, 24, big=3), (4.0, 4.0))

# ---- timber bench planks (CMP: fixed timber benches), grain along u, grey weathered ----
w, h = int(3.0 * PPM), 128
y = np.arange(h)
img = solid(h, w, (150, 138, 120)) + noise(h, w, 8, 10, 30)[..., None] * 0
gr = noise(h, w * 1, 4, 1, 31)
streak = np.array(Image.fromarray(((grain(h, w, 1, 32) + 3) * 40).clip(0, 255).astype(np.uint8)).resize((w // 40, h), Image.BILINEAR).resize((w, h), Image.BICUBIC)).astype(float)
img += ((streak - streak.mean()) * 0.6)[..., None]
img[:6] *= 0.75; img[-6:] *= 0.75                     # plank arrises
for k in range(1, 3): c = int(k * 1.0 * PPM); img[:, c:c + 3] *= 0.6   # board butt joints every 1 m? (screws)
save('bench', img, (3.0, 1.0))

# ---- painted steel (columns, beams, purlins): dark grey enamel ----
save('steel', concrete((58, 60, 62), 1.0, 1.0, 40), (1.0, 1.0))

# ---- painted render / fascia: white paint, joints every 3 m ----
save('white', concrete((226, 223, 219), 3.0, 3.0, 41, joint=3.0, big=2), (3.0, 3.0))
save('render_cream', concrete((214, 202, 188), 3.0, 3.0, 42, joint=3.0, big=2), (3.0, 3.0))   # Social Club upper block, photo (207,195,184) lit
save('plant_pink', concrete((222, 196, 188), 3.0, 3.0, 43, joint=3.0, big=2), (3.0, 3.0))     # roof plant room, photo (214,195,190) lit
save('fascia', concrete((222, 220, 216), 3.0, 1.0, 42, joint=3.0), (3.0, 3.0))

# ---- profiled metal deck (Rush rear): horizontal ribs 200 mm, varies with v ----
img = corrugated((200, 196, 194), 2.0, 2.0, rib=0.2, depth=0.18, seed=43)
save('deck', np.transpose(img, (1, 0, 2)), (2.0, 2.0))

# ---- glazing grids ----
def glazing(wm, hm, mx, my, glass, frame, fw=0.06, seed=50):
    w, h = int(wm * PPM), int(hm * PPM)
    yy = np.arange(h)[:, None] / PPM; xx = np.arange(w)[None, :] / PPM
    g = np.ones((h, w, 3)) * np.array(glass, float)
    g *= (0.9 + 0.2 * (yy / hm))[..., None]                     # sky reflection gradient
    fr = ((xx % mx) < fw) | ((yy % my) < fw)
    g[np.broadcast_to(fr, (h, w))] = frame
    return g + grain(h, w, 2, seed)[..., None]
save('glass', glazing(3.0, 3.5, 1.5, 3.5, (70, 80, 92), (220, 220, 216)), (3.0, 3.5))
save('sher_end', glazing(1.0, 1.0, 0.25, 0.34, (58, 64, 74), (226, 226, 222), fw=0.012), (1.0, 1.0))   # UV 0..1 over the face: 4 x 3 panes
# Social Club east: dark painted panels, 1.2 m wide
img = concrete((84, 84, 96), 2.4, 3.0, 51, joint=1.2)
save('scdark', img, (2.4, 3.0))

# ---- boundary fence: white-painted fence, posts every 2.5 m ----
img = concrete((232, 230, 224), 2.5, 1.0, 52)
img[:, :int(0.1 * PPM)] *= 0.86
img[:int(0.08 * PPM)] *= 0.9
save('fence', img, (2.5, 1.0))
img = concrete((196, 40, 44), 2.5, 1.0, 53, big=3)   # red advertising board (photo red runs along the fence)
img[:, :int(0.1 * PPM)] *= 0.8
img[:int(0.08 * PPM)] = (236, 234, 230); img[-int(0.08 * PPM):] = (236, 234, 230)
save('fence_red', img, (2.5, 1.0))

json.dump(TILE, open('tex3/tile.json', 'w'), indent=1)
print(sorted(TILE))

# ---- Social Club north face (reference zoom): 9 x 7 white panels on a dark frame, a few panels maroon; plain white margin strips each side are separate faces (sc_north_white)
cw, ch, cpx, cpy = 9, 7, 360, 220
w, h = cw * cpx, ch * cpy
img = solid(h, w, (58, 60, 68)) + noise(h, w, 40, 4, 62)[..., None]          # dark enamel spandrel panels
for i in range(1, cw): img[:, i * cpx - 2:i * cpx + 2] *= 0.75                 # panel joints
for j in range(1, ch): img[j * cpy - 2:j * cpy + 2] *= 0.75
RED = {(2, 2), (2, 3), (1, 6), (1, 7), (2, 7)}
for i in range(cw):
    for j in range(ch):
        x0, x1, y0, y1 = i * cpx + 60, (i + 1) * cpx - 60, j * cpy + 26, (j + 1) * cpy - 26
        img[y0 - 6:y1 + 6, x0 - 6:x1 + 6] = (236, 236, 232)                    # white window frame
        if (j, i) in RED:
            pane = np.array([150, 52, 56.])                                      # maroon curtain behind glass
        else:
            pane = np.array([214, 222, 228.])                                    # pale glass, sky reflection
        yy = np.linspace(0, 1, y1 - y0)[:, None, None]
        img[y0:y1, x0:x1] = pane * (1.04 - 0.12 * yy)
        xm = (x0 + x1) // 2; img[y0:y1, xm - 3:xm + 3] = (236, 236, 232)          # centre mullion
        img[y1 + 6:y1 + 12, x0 - 10:x1 + 10] = (246, 246, 242)                   # sill
img += grain(h, w, 2, 60)[..., None]
save('chequer', img, (1.0, 1.0))

# ---- Ryder stand rear (reference zoom + CMP 15 bays): face brick between lighter piers, a small window high in each
# bay, cream parapet band on top; v runs down from the parapet (m), u one bay = 5.24 m (78.6 m of rear wall / 15)
P2 = 128; bwm, hm = 5.24, 10.5; w, h = int(bwm * P2), int(hm * P2)
img = solid(h, w, (205, 198, 188))
for r in range(int(hm / 0.086) + 1):
    y0 = int(r * 0.086 * P2); y1 = int((r * 0.086 + 0.076) * P2)
    off = 0 if r % 2 == 0 else 0.12
    for c in range(-1, int(bwm / 0.24) + 2):
        x0 = int((c * 0.24 + off) * P2); x1 = int((c * 0.24 + off + 0.23) * P2)
        xa, xb = max(0, x0), min(w, x1)
        if xb > xa: img[y0:y1, xa:xb] = np.array([172, 100, 82.]) * (0.88 + 0.24 * rng.random())
pw = int(0.7 * P2)
img[:, :pw] = img[:, :pw] * 0.35 + np.array([214, 176, 160.]) * 0.65          # pier (lighter brick)
img[:, pw:pw + 3] *= 0.75
img[:int(0.8 * P2)] = np.array([222, 214, 200.]) + grain(int(0.8 * P2), w, 3, 61)[..., None]   # parapet band
img[int(0.8 * P2):int(0.8 * P2) + 4] *= 0.7
wx0, wx1 = int((bwm / 2 + 0.35 - 0.5) * P2), int((bwm / 2 + 0.35 + 0.5) * P2)
img[int(1.6 * P2):int(2.8 * P2), wx0:wx1] = (48, 46, 50)
img[int(2.8 * P2):int(2.9 * P2), wx0 - 6:wx1 + 6] = (214, 206, 192)            # sill
save('brick_ry', img, (bwm, hm))
json.dump(TILE, open('tex3/tile.json', 'w'), indent=1)
