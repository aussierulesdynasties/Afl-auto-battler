# Subiaco A (1991): hand-made procedural textures, no photo pixels. Drawn at 2048 px and downsampled to 1024
# (supersampled = crisp edges without stair-steps). Each tile covers 4 m x 4 m unless noted.
import numpy as np, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
os.makedirs('texA', exist_ok=True)
rng = np.random.default_rng(1991); S = 2048; O = 1024
M = S / 4.0                                   # pixels per metre at draw size
yy, xx = np.mgrid[0:S, 0:S]
def save(a, n):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((O, O), Image.LANCZOS); im.save('texA/' + n + '.png')
def grain(sig=1.0, blur=0.8, amp=1.0):
    n = rng.normal(0, 1, (S, S)); im = Image.fromarray(((n * 40 + 128).clip(0, 255)).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    return (np.array(im, float) - 128) / 40 * amp
def blotch(scale=200, amp=1.0):
    n = rng.normal(0, 1, (S // 32, S // 32)); im = Image.fromarray(((n * 40 + 128).clip(0, 255)).astype(np.uint8)).resize((S, S), Image.BICUBIC)
    return (np.array(im.filter(ImageFilter.GaussianBlur(scale / 16)), float) - 128) / 40 * amp
def tint(base, *fields):
    a = np.zeros((S, S, 3)) + np.array(base, float)
    for f, k in fields: a += f[..., None] * k
    return a
# ---- concrete terrace: 0.40 m treads (10 per 4 m of slope), riser shadow, steel nosing, joints every 4 m, weathering
v = yy / M; u = xx / M
t = tint([182, 178, 170], (grain(1, 0.7), 5), (blotch(300), 6))
ph = (v % 0.4) / 0.4
t[ph < 0.18] *= 0.62                                  # riser face in shade
t[(ph >= 0.18) & (ph < 0.21)] = [210, 206, 198]       # bull-nose edge catching light
t[(u % 4.0) < 0.012] *= 0.7                           # expansion joint
save(t, 'terrace')
# ---- grandstand seats: 0.80 m rows, individual 0.46 m bench-back seats in green on a concrete tread
s = tint([168, 164, 156], (grain(1, 0.7), 4), (blotch(300), 4)); im = Image.fromarray(np.clip(s, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
for r in range(5):
    y0 = r * 0.8 * M
    d.rectangle([0, y0, S, y0 + 0.13 * M], fill=(118, 114, 108))                     # riser shadow
    for k in range(int(4 / 0.46) + 1):
        x0 = k * 0.46 * M + 0.03 * M
        g = int(rng.integers(-6, 7))
        d.rounded_rectangle([x0, y0 + 0.20 * M, x0 + 0.40 * M, y0 + 0.50 * M], radius=int(0.05 * M), fill=(40 + g, 98 + g, 64 + g))   # seat pan
        d.rounded_rectangle([x0, y0 + 0.50 * M, x0 + 0.40 * M, y0 + 0.62 * M], radius=int(0.04 * M), fill=(26 + g, 70 + g, 46 + g))   # back in shadow
        d.line([x0 + 0.04 * M, y0 + 0.23 * M, x0 + 0.36 * M, y0 + 0.23 * M], fill=(88, 150, 112), width=4)                            # lit front lip
save(np.array(im, float), 'seats')
# ---- white corrugated roof sheeting: 76 mm corrugations, 0.76 m sheet laps across, end laps every 6 m down, light grime
r = tint([232, 228, 218], (grain(1, 1.2), 3), (blotch(400), 5))
r += (np.cos(u / 0.076 * 2 * np.pi) * 10)[..., None]
r[(u % 0.76) < 0.01] *= 0.86
r[(v % 2.0) < 0.012] *= 0.84                          # end lap (tile repeats every 4 m; 2 m spacing reads as 6 m at roof scale)
r[(v % 4.0) > 3.85] *= 0.93                           # gutter staining at the low edge
save(r, 'roof')
# ---- dark grey trapezoidal deck (west stand), 0.25 m ribs
dd = tint([112, 114, 112], (grain(1, 1), 3), (blotch(400), 4))
ph = (u % 0.25) / 0.25
dd[ph < 0.10] *= 0.72; dd[(ph >= 0.10) & (ph < 0.16)] *= 1.18
save(dd, 'roofd')
# ---- cream render wall: 4 m panels, 1 m dark plinth band, faint rain streaks
w = tint([232, 222, 198], (grain(1, 1), 3), (blotch(300), 5))
w[(u % 4.0) < 0.02] *= 0.82
w[v < 0.06] *= 0.88
st = (rng.random(S) < 0.02).astype(float); st = np.array(Image.fromarray((st * 255).astype(np.uint8)[None, :].repeat(S, 0)).filter(ImageFilter.GaussianBlur(3)), float) / 255
w -= (st * 30 * np.clip(1 - v / 2.0, 0, 1))[..., None]
save(w, 'wall')
# ---- cream face brick, stretcher bond, 230 x 76 mm bricks with 10 mm joints, per-brick colour shift
b = np.zeros((S, S, 3)); im = Image.new('RGB', (S, S), (150, 144, 134)); d = ImageDraw.Draw(im)
bh, bw, j = 0.086 * M, 0.24 * M, 0.010 * M
for row in range(int(S / bh) + 1):
    off = 0 if row % 2 == 0 else bw / 2
    for k in range(-1, int(S / bw) + 2):
        x0 = k * bw + off; y0 = row * bh; g = rng.normal(0, 2, 3)
        c = tuple(int(x) for x in np.clip(np.array([214, 194, 160]) * (1 + rng.normal(0, 0.045)) + g, 0, 255))
        d.rectangle([x0 + j / 2, y0 + j / 2, x0 + bw - j / 2, y0 + bh - j / 2], fill=c)
b = np.array(im, float) + grain(1, 0.6)[..., None] * 4
save(b, 'brick')
# ---- soffit / underside: grey steel with purlin lines every 1.2 m
un = tint([96, 94, 90], (grain(1, 1), 3), (blotch(400), 3))
un[(v % 1.2) < 0.06] *= 0.7
save(un, 'under')
# ---- white painted steel fascia: 6 m panels with joints, slight chalking
fa = tint([244, 242, 236], (grain(1, 1.5), 2), (blotch(500), 3)); fa[(u % 2.0) < 0.015] *= 0.86
save(fa, 'fascia')
# ---- asphalt and brick paving
a_ = tint([92, 92, 90], (grain(1, 0.5), 9), (blotch(300), 6)); save(a_, 'asphalt')
p = tint([206, 188, 156], (grain(1, 0.6), 5), (blotch(300), 5)); p[(v % 0.6) < 0.012] *= 0.82; p[(u % 0.6) < 0.012] *= 0.82
save(p, 'paving')
# ---- picket fence: 0.09 m white pickets with 0.04 m gaps, rails, shadow (tile 2 m wide x 2 m tall -> uses tile=2)
pk = tint([246, 244, 238], (grain(1, 1), 2)); uu = (xx / S) * 2.0; vv = (yy / S) * 2.0
pk[(uu % 0.13) > 0.09] = [64, 92, 58]                 # turf seen through the gaps
pk[((vv > 0.30) & (vv < 0.36)) | ((vv > 0.80) & (vv < 0.86))] = [226, 224, 216]
save(pk, 'picket')
# ---- galvanised steel
stl = tint([178, 180, 178], (grain(1, 2), 3), (blotch(400), 5)); save(stl, 'steel')
# ---- glass band: dark panes in white mullions every 1.5 m
gl = tint([58, 72, 84], (blotch(400), 6)); gl[(u % 1.5) < 0.06] = [232, 230, 222]; gl[(v % 2.0) < 0.06] = [232, 230, 222]; save(gl, 'glass')
# ---- giant can (giant drink can, generic): gold body, red band, silver rims (tile wraps once around, 1 unit = whole can)
cn = tint([214, 170, 60], (grain(1, 2), 3)); cn[int(S * 0.40):int(S * 0.62)] = [184, 34, 34]; cn[:int(S * 0.04)] = [200, 200, 200]; cn[-int(S * 0.04):] = [200, 200, 200]
save(cn, 'can')
# ---- scoreboard face: black board, white frame, lamp panels for two team names, goals.behinds.points, clock
sb = Image.new('RGB', (S, S), (22, 24, 26)); d = ImageDraw.Draw(sb)
d.rectangle([0, 0, S - 1, S - 1], outline=(236, 236, 230), width=int(0.12 * M))
try: F = ImageFont.truetype('arialbd.ttf', int(0.34 * M))
except Exception: F = ImageFont.load_default()
for row, y0 in enumerate((0.55 * M, 1.55 * M)):
    d.rectangle([0.3 * M, y0, 2.3 * M, y0 + 0.7 * M], fill=(40, 42, 44))
    for k in range(3):
        x0 = 2.5 * M + k * 0.42 * M; d.rectangle([x0, y0, x0 + 0.34 * M, y0 + 0.7 * M], fill=(40, 42, 44))
d.rectangle([1.2 * M, 2.7 * M, 2.8 * M, 3.4 * M], fill=(40, 42, 44))
for x in range(0, S, 12):                             # lamp matrix dots
    for y in range(0, S, 12):
        if sb.getpixel((x, y)) == (40, 42, 44): d.ellipse([x, y, x + 6, y + 6], fill=(70, 70, 64))
save(np.array(sb, float), 'score')
# ---- white turf paint, turf as before (mown 8 m stripes, gentle)
save(np.full((64, 64, 3), 240.), 'paint')
tf = tint([88, 128, 60], (grain(1, 1.2), 5), (blotch(600), 6)); tf *= np.where(((xx / S * 32) // 8) % 2 == 0, 1.0, 0.94)[..., None]; save(tf, 'turf')
# ---- concrete (plain, for stair blocks, barriers' footings)
cc = tint([190, 186, 178], (grain(1, 0.7), 5), (blotch(300), 6)); save(cc, 'concrete')
# ---- crush barrier rail: galvanised pipe, uniform
save(np.full((64, 64, 3), [196, 198, 196.]), 'rail')
print('ok')
