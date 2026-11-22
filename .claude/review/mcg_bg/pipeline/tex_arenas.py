"""Hand-made arena textures for Melbourne Park (drawn from the aerial; no photo pixels). Appends to tex/lm_sizes.json."""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(HERE, 'tex')
rng = np.random.default_rng(7)
SIZES = json.load(open(os.path.join(T, 'lm_sizes.json')))
def noise(h, w, amp, blur=1.5):
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    im = Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    return (np.asarray(im, np.float32) - 128) / 40 * amp
def save(nm, a, tile):
    a = np.clip(a, 0, 255).astype(np.uint8); Image.fromarray(a).save(os.path.join(T, nm))
    g = a[..., :3].astype(np.float32) @ np.array([0.299, 0.587, 0.114]); SIZES[nm] = tile
    print(nm, a.shape[1], 'x', a.shape[0], 'tile', tile, 'grey std %.1f' % g.std())
PX = 32
# arena wall: white precast panels 3 m x 3 m over a dark glazed band (bottom 4 m), 12 m tall tile, 12 m wide
w, h = 12 * PX, 12 * PX; a = np.zeros((h, w, 3), np.float32) + (226, 226, 222)
for i in range(4):   # panel joints every 3 m
    a[:, i * 3 * PX:i * 3 * PX + 2] = (150, 152, 152); a[i * 3 * PX:i * 3 * PX + 2] = (150, 152, 152)
a[h - 4 * PX:] = (52, 62, 70)
for x in range(0, w, int(1.5 * PX)): a[h - 4 * PX:, x:x + 3] = (120, 124, 126)
a[h - 4 * PX - 6:h - 4 * PX] = (90, 92, 94)
for x in range(0, w, int(0.75 * PX)): a[int(5 * PX):int(5.6 * PX), x:x + 14] = (70, 80, 88)   # louvre strip
a += noise(h, w, 6)[..., None]; a[:h - 4 * PX] += rng.normal(0, 4, (1, 1, 3)); a[::-1] = a[::-1]
save('lm_arena_wall.png', a[::-1][::-1], [12, 12])
# copper roof / wall: standing seam 0.5 m, sheets 6 m, maroon-brown corrugated (photo 124 roof samples ~ (95,60,57))
w, h = 12 * PX, 12 * PX; a = np.zeros((h, w, 3), np.float32) + (90, 54, 50)
for x in range(0, w, PX // 2): a[:, x:x + 2] = (70, 40, 37); a[:, x + 2:x + 4] = (108, 68, 62)
for y in range(0, h, 6 * PX): a[y:y + 2] = (74, 42, 39)
for x in range(0, w, PX // 2): a[:, x:x + PX // 2] *= 1 + 0.06 * (rng.random() - 0.5)
a += noise(h, w, 7, 3)[..., None]; save('lm_copper.png', a, [12, 12])
# white ribbed roof sheet (seams every 0.6 m, ribs every 6 m), tile 12 m
w, h = 12 * PX, 12 * PX; a = np.zeros((h, w, 3), np.float32) + (214, 214, 208)
for x in range(0, w, int(0.6 * PX)): a[:, x:x + 2] = (176, 176, 172)
for x in range(0, w, 6 * PX): a[:, x:x + 6] = (150, 152, 150); a[:, x + 6:x + 9] = (240, 240, 236)
a += noise(h, w, 6, 4)[..., None]
for _ in range(10):
    cx = rng.integers(0, w); a[:, max(0, cx - 4):cx + 4] -= 8   # drain streaks
save('lm_ribwhite.png', a, [12, 12])
# glazed roof: pale blue-grey panes 2 x 3 m, white mullions, dark truss shadow every 9 m
w, h = 18 * PX, 18 * PX; a = np.zeros((h, w, 3), np.float32) + (150, 168, 176)
for y in range(0, h, 3 * PX):
    for x in range(0, w, 2 * PX): a[y:y + 3 * PX, x:x + 2 * PX] += rng.normal(0, 7)
for x in range(0, w, 2 * PX): a[:, x:x + 3] = (232, 232, 228)
for y in range(0, h, 3 * PX): a[y:y + 3] = (232, 232, 228)
for x in range(0, w, 9 * PX): a[:, x:x + 10] = (96, 100, 104)
a += noise(h, w, 5)[..., None]; save('lm_glazed.png', a, [18, 18])
# AAMI Park bioframe shell: white triangular panels (2.4 m) with grey steel lines and soft shading
w, h = 12 * PX, 12 * PX; im = Image.new('RGB', (w, h), (236, 236, 232)); d = ImageDraw.Draw(im); s = int(2.4 * PX)
for y in range(-s, h + s, s):
    for x in range(-s, w + s, s):
        off = (y // s % 2) * s // 2
        tri = [(x + off, y), (x + off + s, y), (x + off + s // 2, y + s)]
        g = int(rng.integers(214, 244)); d.polygon(tri, fill=(g, g, g - 3), outline=(150, 154, 156))
        tri2 = [(x + off + s // 2, y + s), (x + off + s, y), (x + off + 3 * s // 2, y + s)]
        g = int(rng.integers(214, 244)); d.polygon(tri2, fill=(g, g, g - 3), outline=(150, 154, 156))
a = np.asarray(im, np.float32) + noise(h, w, 5)[..., None]; save('lm_bubble.png', a, [12, 12])
# empty seat tiers: navy/blue seat rows every 0.8 m with grey concrete risers
w, h = 8 * PX, 8 * PX; a = np.zeros((h, w, 3), np.float32) + (120, 122, 124)
for y in range(0, h, int(0.8 * PX)): a[y:y + int(0.5 * PX)] = (34, 58, 112)
for x in range(0, w, int(0.5 * PX)): a[:, x:x + 2] -= 18
a += noise(h, w, 6)[..., None]; save('lm_tiers.png', a, [8, 8])
# pitch: rectangular soccer/rugby turf, mowing bands every 6 m
w, h = 12 * PX, 12 * PX; a = np.zeros((h, w, 3), np.float32) + (62, 116, 52)
a[:, :6 * PX] *= 0.8; a += noise(h, w, 9, 2)[..., None]; save('lm_pitch.png', a, [12, 12])
# John Cain Arena wall (photos: Commons Melbourne Park 007/010/011/014, Olympic Park 013): glazed concourse 0-7 m with
# mullions every 1.5 m, white canopy fascia 7-8 m, pale-blue cladding panels 3 m wide 8-17 m with a teal window strip
# at 12-13 m, white parapet 17-18 m. Tile 12 m wide x 18 m tall (row 0 = top).
w, h = 12 * PX, 18 * PX; a = np.zeros((h, w, 3), np.float32)
def band(z0, z1, rgb): a[h - int(z1 * PX):h - int(z0 * PX)] = rgb
# photo JCA.jpg (south face from Olympic Blvd): the lower storey is the same pale panel cladding as above (shade ratio 0.9),
# 3 m panels, a dark window strip 4.0-4.6 m, columns every 6 m; no dark glazed base
for i in range(4):
    c = (np.array((176, 188, 200)) + rng.normal(0, 6, 3)) * 0.9; a[h - 7 * PX:, i * 3 * PX:(i + 1) * 3 * PX] = c
    a[h - 7 * PX:, i * 3 * PX:i * 3 * PX + 2] = (120, 140, 156)
band(4.0, 4.6, (14, 18, 32))
for x in range(0, w, 6 * PX): a[h - 7 * PX:, x:x + int(0.6 * PX)] = (176, 184, 190)
band(7, 8, (232, 234, 234))
for i in range(4):
    c = np.array((176, 188, 200)) + rng.normal(0, 6, 3); a[h - 17 * PX:h - 8 * PX, i * 3 * PX:(i + 1) * 3 * PX] = c
    a[h - 17 * PX:h - 8 * PX, i * 3 * PX:i * 3 * PX + 2] = (120, 140, 156)
band(12, 13, (70, 150, 160))
for x in range(0, w, int(1.5 * PX)): a[h - 13 * PX:h - 12 * PX, x:x + 2] = (200, 210, 214)
band(17, 18, (236, 238, 238))
a += noise(h, w, 4)[..., None]; save('lm_jca_wall.png', a, [12, 18])
# John Cain signage crown (photos Melbourne Park 011/007, MCG OIC): silver-grey panels, black "JOHN CAIN" over "ARENA",
# lettering drawn here by hand with a bold sans; crown 3.5 m tall; ring tile = drum circumference (r 17 m), text centred at f.
def sign_tile(wm, f, nm):
    w, h = int(wm * PX), int(3.5 * PX); im = Image.new('RGB', (w, h), (190, 196, 200)); d = ImageDraw.Draw(im)
    for x in range(0, w, int(1.2 * PX)): d.line([(x, 0), (x, h)], fill=(168, 174, 178), width=2)
    from PIL import ImageFont
    F1 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', int(1.55 * PX)); cx = int(f * w)
    for txt, y, wid in (('JOHN CAIN', int(0.1 * PX), 17.0), ('ARENA', int(1.75 * PX), 12.5)):   # photo 011: JOHN CAIN ~17 m wide, ARENA ~12.5 m
        bb = d.textbbox((0, 0), txt, font=F1); lay = Image.new('L', (bb[2] - bb[0], bb[3])); ImageDraw.Draw(lay).text((-bb[0], 0), txt, font=F1, fill=255)
        lay = lay.resize((int(wid * PX), lay.height)); im.paste((28, 30, 34), (cx - lay.width // 2, y), lay)
    a = np.asarray(im, np.float32)[::-1]; save(nm, a[::-1] + noise(h, w, 3)[..., None], [wm, 3.5])
sign_tile(2 * np.pi * 17, 0.1365, 'lm_jca_sign.png')   # text centred on the drum's 29.2 m arc (ring starts at the arc's south end); sign_tile(2 * np.pi * 21, 0.5, 'lm_jca_signq.png')
# Rod Laver Arena facade (Commons Melbourne Park 019/020, people 1.75 m -> 37 px/m): dark entry glazing 0-3.5 m, white canopy
# fascia 3.5-4.5 m, reflective blue curtain glass 4.5-11.5 m (mullions 1.5 m, transoms 2.3 m), white roof fascia 11.5-12.5 m. Tile 12 x 12.5 m.
w, h = 12 * PX, int(12.5 * PX); a = np.zeros((h, w, 3), np.float32)
def bnd(z0, z1, rgb): a[h - int(z1 * PX):h - int(z0 * PX)] = rgb
bnd(0, 3.5, (40, 46, 52)); bnd(3.5, 4.5, (236, 238, 238))
for i in range(8):
    zz = 4.5 + i * 0.875 * 1.0; c = np.array((70, 104, 132)) + rng.normal(0, 7, 3); bnd(4.5 + i * 0.875, 4.5 + (i + 1) * 0.875, c)
bnd(11.5, 12.5, (236, 238, 238))
for x in range(0, w, int(1.5 * PX)): a[h - int(11.5 * PX):h - int(4.5 * PX), x:x + 2] = (190, 196, 200); a[h - int(3.5 * PX):, x:x + 3] = (120, 124, 128)
for zz in (6.8, 9.1): a[h - int(zz * PX):h - int(zz * PX) + 2, :] = (190, 196, 200)
save('lm_rla_wall.png', a + noise(h, w, 3)[..., None], [12, 12.5])
# Margaret Court facade (Commons Melbourne Park 124): blue/white diamond band 0-2.5 m, glass with white and grey triangle panels
# 2.5-10.5 m, orange edge 11.6-12 m over white fascia 10.5-11.6 m. Tile 12 x 12 m.
w, h = 12 * PX, 12 * PX; im = Image.new('RGB', (w, h), (52, 66, 80)); d = ImageDraw.Draw(im)
s = int(1.5 * PX); y0 = h - int(2.5 * PX)
for x in range(0, w, s):
    d.polygon([(x, h), (x + s, h), (x + s, y0)], fill=(40, 120, 200)); d.polygon([(x, h), (x, y0), (x + s, y0)], fill=(236, 240, 242))
for x in range(0, w, int(1.5 * PX)): d.line([(x, h - int(10.5 * PX)), (x, y0)], fill=(150, 156, 160), width=2)
for k, x in enumerate(range(0, w, s)):
    if k % 3 == 0:
        for yy in range(int(1.5 * PX), y0 - s, s): d.polygon([(x, yy), (x + s, yy + s), (x, yy + s)], fill=(222, 226, 228) if (yy // s) % 2 else (150, 156, 162))
d.rectangle([0, 0, w, int(0.4 * PX)], fill=(214, 120, 52)); d.rectangle([0, int(0.4 * PX), w, int(1.5 * PX)], fill=(232, 234, 230))   # photo 124: orange roof edge over a white fascia
save('lm_mca_wall.png', np.asarray(im, np.float32) + noise(h, w, 3)[..., None], [12, 12])
json.dump(SIZES, open(os.path.join(T, 'lm_sizes.json'), 'w'), indent=1)
