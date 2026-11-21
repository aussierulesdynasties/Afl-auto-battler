# Hand-made facade tiles, one bay (3.6 m) x one floor (3.2 m) = 288 x 256 px (80 px/m). Never photo pixels.
import numpy as np, os, sys
from PIL import Image
rng = np.random.default_rng(3); W, H = 288, 256; ppm = 80; OUT = sys.argv[1]
def noise(a=0.04): return 1 + a * rng.standard_normal((H, W, 1))
def save(n, img): Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).save(os.path.join(OUT, n)); print(n, round(float(np.clip(img*255,0,255).std()),1))
gy, gx = np.mgrid[0:H, 0:W]
# 1 heritage brick: red-brown stretcher bond, cream render sill/lintel, tall sash window with white frame and glazing bars
b = np.zeros((H, W, 3)); course = 0.086 * ppm; brick_l = 0.23 * ppm
row = (gy // course).astype(int); off = (row % 2) * brick_l / 2
bid = row * 1000 + ((gx + off) // brick_l).astype(int); tone = rng.uniform(0.82, 1.12, bid.max() + 1)
b[:] = np.array([0.55, 0.27, 0.19]) * tone[bid][..., None]
mortar = ((gy % course) < 1.2) | (((gx + off) % brick_l) < 1.2); b[mortar] = [0.72, 0.68, 0.6]
x0, x1, y0, y1 = int(1.1 * ppm), int(2.5 * ppm), int(0.45 * ppm), int(2.65 * ppm)
b[y0 - 10:y0, x0 - 8:x1 + 8] = [0.86, 0.82, 0.72]; b[y1:y1 + 10, x0 - 8:x1 + 8] = [0.86, 0.82, 0.72]
b[y0:y1, x0:x1] = [0.93, 0.93, 0.9]; g = np.array([0.18, 0.22, 0.26]) * noise(0.08)[y0 + 6:y1 - 6, x0 + 6:x1 - 6]
b[y0 + 6:y1 - 6, x0 + 6:x1 - 6] = g
my = (y0 + y1) // 2; b[my - 3:my + 3, x0:x1] = [0.93, 0.93, 0.9]; mx = (x0 + x1) // 2; b[y0:y1, mx - 2:mx + 2] = [0.93, 0.93, 0.9]
save('fac_brick.png', b * noise(0.03))
# 2 office / hospital: precast concrete spandrel band + continuous ribbon glazing with mullions every 1.2 m
o = np.ones((H, W, 3)) * np.array([0.74, 0.73, 0.7]) * noise(0.035)
gy0, gy1 = int(0.95 * ppm), int(2.85 * ppm)
glass = np.array([0.2, 0.27, 0.32]) + 0.12 * (1 - (gy - gy0) / (gy1 - gy0))[..., None] * np.array([0.6, 0.8, 1])
o[gy0:gy1] = glass[gy0:gy1] * noise(0.03)[gy0:gy1]
for mxp in range(0, W, int(1.2 * ppm)): o[gy0:gy1, mxp:mxp + 5] = [0.42, 0.43, 0.44]
o[gy0 - 4:gy0] *= 0.6; o[gy1:gy1 + 3] = [0.5, 0.5, 0.5]
save('fac_office.png', o)
# 3 apartments: rendered wall, full-height glass door, balcony slab edge and glass balustrade with dark handrail
a = np.ones((H, W, 3)) * np.array([0.84, 0.82, 0.78]) * noise(0.03)
dx0, dx1, dy0 = int(0.4 * ppm), int(3.2 * ppm), int(0.25 * ppm)
a[dy0:H - 22, dx0:dx1] = np.array([0.22, 0.27, 0.3]) * noise(0.05)[dy0:H - 22, dx0:dx1]
for mxp in (dx0, (dx0 + dx1) // 2, dx1 - 4): a[dy0:H - 22, mxp:mxp + 4] = [0.3, 0.3, 0.3]
a[H - 22:] = [0.9, 0.9, 0.88]; a[H - 22:H - 18] = [0.55, 0.55, 0.55]
bal = slice(int(H - 22 - 1.0 * ppm), H - 22); a[bal] = a[bal] * 0.75 + np.array([0.55, 0.62, 0.62]) * 0.25
a[int(H - 22 - 1.0 * ppm):int(H - 22 - 1.0 * ppm) + 4] = [0.2, 0.2, 0.2]
save('fac_apart.png', a)
# 4 arena / sports hall: vertical ribbed metal cladding (ribs every 0.2 m), pale silver-grey, one dark louvre band
c = np.ones((H, W, 3)) * np.array([0.72, 0.74, 0.76])
rib = (gx % int(0.2 * ppm)); c *= (0.86 + 0.18 * np.clip(np.sin(rib / (0.2 * ppm) * np.pi), 0, 1))[..., None]
c[int(2.6 * ppm):int(2.9 * ppm)] = np.array([0.25, 0.27, 0.29]) * (0.85 + 0.15 * ((gy[int(2.6 * ppm):int(2.9 * ppm)] % 6) < 3))[..., None]
save('fac_clad.png', c * noise(0.02))
# ---- CBD tower curtain walls: one bay 3.0 m x one floor 3.6 m = 240 x 288 px. Colours from reference photos of each family's towers.
TW, TH = 240, 288; ty, tx = np.mgrid[0:TH, 0:TW]
def tn(a=0.03): return 1 + a * rng.standard_normal((TH, TW, 1))
def glass(top, bot):   # sky reflection: lighter at the head of each pane
    f = (ty / TH)[..., None]; return (np.array(top) * (1 - f) + np.array(bot) * f) * tn(0.025)
def tower(name, pane_top, pane_bot, spandrel, mull, sp_h, mull_every, mull_w, pier=None, pier_w=0, solid=False):
    t = glass(pane_top, pane_bot); s0 = TH - int(sp_h * ppm)
    for m in range(0, TW, int(mull_every * ppm)): t[:, m:m + mull_w] = mull                  # mullions
    t[s0:] = np.array(spandrel) * tn(0.03)[s0:]                                              # spandrel band at floor slab
    if not solid:
        for m in range(0, TW, int(mull_every * ppm)): t[s0:, m:m + mull_w] = mull
    t[s0:s0 + 3] *= 0.7                                                                      # transom shadow line
    if pier is not None: t[:, :pier_w] = np.array(pier) * tn(0.03)[:, :pier_w]; t[:, pier_w:pier_w + 4] *= 0.65   # stone pier + its shadow
    save(name, t)
tower('twr_blue.png', (0.42, 0.58, 0.70), (0.18, 0.30, 0.40), (0.20, 0.30, 0.38), (0.55, 0.6, 0.64), 0.9, 1.5, 3)                            # blue reflective curtain wall
tower('twr_green.png', (0.38, 0.52, 0.50), (0.16, 0.26, 0.26), (0.22, 0.30, 0.30), (0.6, 0.62, 0.62), 0.9, 1.5, 3)                           # green-tinted glass (ANZ, Sapphire)
tower('twr_silver.png', (0.55, 0.60, 0.64), (0.28, 0.32, 0.36), (0.62, 0.64, 0.66), (0.78, 0.8, 0.82), 0.9, 1.5, 4)                          # silver glass grid
# 5 Victorian terrace, rendered: smooth render (tinted per house in the scene), moulded cornice at the head, tall sash window
#   with a rendered surround and sill, timber frames, a bluestone plinth course at the foot
r_ = np.ones((H, W, 3)) * np.array([0.88, 0.85, 0.78]) * noise(0.025)
r_[(gy % int(0.45 * ppm)) < 1] *= 0.93                                         # ashlar lines ruled in the render
r_[:14] = np.array([0.93, 0.91, 0.86]); r_[14:18] *= 0.62; r_[4:6] *= 0.8      # cornice and its shadow
x0, x1, y0, y1 = int(1.15 * ppm), int(2.45 * ppm), int(0.55 * ppm), int(2.7 * ppm)
r_[y0 - 12:y1 + 12, x0 - 12:x1 + 12] = [0.95, 0.94, 0.9]; r_[y1 + 8:y1 + 14, x0 - 18:x1 + 18] = [0.72, 0.7, 0.66]   # surround, sill
r_[y0:y1, x0:x1] = [0.92, 0.92, 0.88]
r_[y0 + 6:y1 - 6, x0 + 6:x1 - 6] = np.array([0.16, 0.19, 0.22]) * noise(0.08)[y0 + 6:y1 - 6, x0 + 6:x1 - 6]
my = (y0 + y1) // 2; r_[my - 4:my + 4, x0:x1] = [0.92, 0.92, 0.88]
r_[H - 8:] = np.array([0.82, 0.8, 0.74]); r_[H - 8:H - 6] *= 0.8                # string course at each floor line
save('fac_render.png', r_)
# ---- named towers, from reference photos in scratchpad/towerref (colours are the photo's sunlit-wall and glass medians; ratios read off the crops)
def c255(c): return np.array(c) / 255
def punched(name, wall, glass_c, wfrac, hfrac, pairs=1, reveal=0.75):
    t = np.ones((TH, TW, 3)) * c255(wall) * tn(0.03)
    ww = int(TW * wfrac / pairs); wh = int(TH * hfrac); y0 = (TH - wh) // 2
    for k in range(pairs):
        x0 = int((k + 0.5) * TW / pairs - ww / 2)
        t[y0 - 4:y0 + wh + 4, x0 - 4:x0 + ww + 4] *= reveal                      # reveal shadow round the opening
        t[y0:y0 + wh, x0:x0 + ww] = glass(c255(glass_c) * 1.25, c255(glass_c) * 0.8)[y0:y0 + wh, x0:x0 + ww]
    save(name, t)
def ribbon(name, wall, glass_c, band, mull_every, pil=0, pil_c=None, sill=None):
    t = np.ones((TH, TW, 3)) * c255(wall) * tn(0.03); wh = int(TH * band); y0 = int(TH * 0.12)
    t[y0:y0 + wh] = glass(c255(glass_c) * 1.25, c255(glass_c) * 0.8)[y0:y0 + wh]
    for m in range(0, TW, int(mull_every * ppm)): t[y0:y0 + wh, m:m + 4] = c255(wall) * 0.8
    if sill: t[y0 + wh:y0 + wh + 10] = c255(sill)
    if pil: t[:, :int(pil * ppm)] = c255(pil_c or wall) * tn(0.03)[:, :int(pil * ppm)]; t[:, int(pil * ppm):int(pil * ppm) + 4] *= 0.7
    save(name, t)
punched('twr_c120.png', (151, 130, 99), (63, 56, 51), 0.42, 0.72, pairs=1)                  # photo crop c120_z: square grid, window 0.55 of pitch each way (tile = 3.9 m pitch x 4.27 m floor)
ribbon('twr_c101.png', (119, 125, 131), (54, 89, 123), 0.45, 1.0, pil=0.6, pil_c=(132, 138, 144))                          # c101 crop: grey spandrels, ribbon glass 0.45 of floor, mullions every 1 m
punched('twr_cplace.png', (158, 153, 146), (81, 97, 109), 0.87, 0.65, pairs=1, reveal=0.85)   # cp_z: wide panes (2:1), thin mullions; tile = 6.0 m pitch x floor
ribbon('twr_spring.png', (201, 199, 192), (26, 29, 31), 0.50, 1.0, pil=0.3, sill=(220, 218, 212))   # spring crop: pier every 3 m, white sill under each glass band
# Nauru House: concrete with a deep horizontal sun-shade fin over dark recessed glass on every floor
t = ribbon_t = np.ones((TH, TW, 3)) * c255((150, 146, 140)) * tn(0.03)
gy0, gy1 = int(TH * 0.30), int(TH * 0.74); t[gy0:gy1] = glass(c255((49, 49, 48)) * 1.2, c255((49, 49, 48)) * 0.8)[gy0:gy1]
t[gy0 - 30:gy0] = c255((170, 166, 158)); t[gy0:gy0 + 22] *= 0.45                            # fin face + its shadow on the glass
save('twr_nauru.png', t)

# landmark copies for the hand-built crowns (landmarks.py): same tiles, sizes = 3.0 m bay x the tower's floor height (roof height / floor count)
import json, shutil
SZ = json.load(open(os.path.join(OUT, 'lm_sizes.json')))
for k, fh in (('c120', 222 / 52), ('c101', 195 / 57), ('nauru', 183 / 52)):
    shutil.copy(os.path.join(OUT, 'twr_%s.png' % k), os.path.join(OUT, 'lm_%s.png' % k)); SZ['lm_%s.png' % k] = [3.9 if k == 'c120' else 3.0, round(fh, 3)]
g = np.ones((TH, TW, 3)) * glass(c255((54, 89, 123)) * 1.3, c255((54, 89, 123)) * 0.8)            # 101 Collins central glazed strip and crown: blue curtain glass, thin mullions
g[:, ::60] = c255((150, 156, 162)); g[::int(TH * 0.5)] = c255((150, 156, 162)); save('lm_c101_glass.png', g); SZ['lm_c101_glass.png'] = [3.0, round(195 / 57, 3)]
sl = np.ones((TH, TW, 3)) * c255((40, 40, 40)) * tn(0.03); sl[::int(TH)] = 0.3; save('lm_slot.png', sl); SZ['lm_slot.png'] = [3.0, 3.52]   # Nauru central slot: deep shadowed recess
json.dump(SZ, open(os.path.join(OUT, 'lm_sizes.json'), 'w'), indent=1)

def curtain(name, glass_c, mull_c, cols, rows):
    t = glass(c255(glass_c) * 1.12, c255(glass_c) * 0.88) * tn(0.02)
    for k in range(cols): t[:, int(k * TW / cols):int(k * TW / cols) + 3] = c255(mull_c)
    for k in range(rows): t[int(k * TH / rows):int(k * TH / rows) + 3] = c255(mull_c)
    save(name, t)
curtain('twr_tac.png', (160, 190, 211), (60, 66, 76), 2, 2)          # TAC House (tac.jpg): pale blue mirror glass, square panels, dark mullions
curtain('twr_cass.png', (128, 143, 157), (165, 172, 178), 2, 2)      # Casselden (cass.jpg crop median): blue-grey glass, light spandrel line each half floor
curtain('twr_sx1.png', (46, 78, 150), (30, 40, 70), 2, 2)            # SX1 (sx1.jpg): deep blue reflective curtain wall, square panels
ribbon('twr_sapph.png', (225, 228, 232), (60, 95, 150), 0.86, 1.5)   # Sapphire (sapphire.jpg): blue glass floor to floor, thin white slab edge each floor
punched('twr_hwt.png', (150, 106, 96), (95, 150, 140), 0.50, 0.56, pairs=1)   # HWT (hwt.jpg): pink-brown granite, small square teal windows
punched('twr_regency.png', (224, 212, 190), (66, 108, 148), 0.56, 0.60, pairs=1, reveal=1.12)   # Regency (r5crop): pale cream render, blue glass, white frame round each window
# Regency balconies are geometry now (scene.py, from the CoM outline's stacks); the wall keeps plain punched windows.
# Regency podium (r5.jpg, r1.jpg, r20.jpg): pale sandstone panels, joints on a ~1.5 m x 1.3 m grid, one small dark-green square window per bay
pf = TH; t = np.ones((TH, TW, 3)) * c255((214, 206, 190)) * tn(0.03)
for jx in range(0, TW, int(1.5 * ppm)): t[:, jx:jx + 2] *= 0.8
for jy in range(0, TH, int(1.3 * ppm)): t[jy:jy + 2] *= 0.8
# r5crop: podium mostly blank stone; small dark-green windows in one column only (left third of the tile)
w0, w1 = int(0.3 * ppm), int(1.1 * ppm); h0, h1 = int(1.4 * ppm), int(2.2 * ppm)
t[h0:h1, w0:w1] = c255((40, 70, 58)) * tn(0.03)[h0:h1, w0:w1]; t[h0 - 3:h0, w0:w1] *= 0.6
from PIL import Image as _I
save('twr_regpod.png', t)
