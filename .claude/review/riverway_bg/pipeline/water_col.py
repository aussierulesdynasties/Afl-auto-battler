"""data/<g>/prep/water_col.png: hand-made river colour map for the scene's water surface (wrapped so uv = xy / (2 NE)).
Ross River olive-brown: lighter within ~6 m of the bank, darker mid-channel, long ripple streaks running parallel to the
banks (i.e. along the flow; bands of distance-to-bank, ~20 m repeat, broken by along-flow drift and a second scale).
Mask = OSM natural=water outlines. python -E water_col.py spec.json"""
import sys, json, math, numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt
sp = json.load(open(sys.argv[1])); name = sp['name']; D = 'data/%s/prep/' % name
NE = sp['near_half_m']; N = 4096; px = 2 * NE / N
lat0, lon0 = sp['lat'], sp['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
els = json.load(open('data/%s/osm.json' % name, encoding='utf-8'))['elements']
mi = Image.new('L', (N, N), 0); dr = ImageDraw.Draw(mi)
for el in els:
    if el.get('type') != 'way' or el.get('tags', {}).get('natural') != 'water': continue
    P = [((p['lon'] - lon0) * KX, (p['lat'] - lat0) * KY) for p in (el.get('geometry') or []) if p]
    if len(P) < 4: continue
    dr.polygon([((x + NE) / px, (NE - y) / px) for x, y in P], fill=255)   # row 0 = north
m = np.asarray(mi) > 0
d = distance_transform_edt(m) * px   # metres from the bank
rng = np.random.default_rng(3)
def noise(s):   # smooth value noise, cell s px
    a = rng.random((N // s + 3, N // s + 3)); return np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize(((N // s + 3) * s,) * 2, Image.BICUBIC), float)[:N, :N] / 255
base = np.array(sp['palette'].get('river_paint', [70, 72, 55]), float)
drift = noise(160) * 25.0 + noise(48) * 4.0            # along-flow drift of the bands (repeat break)
ph = 2 * math.pi * (d + drift)
streak = 0.55 * np.sin(ph / 20.0) + 0.30 * np.sin(ph / 7.3 + 1.7) + 0.15 * np.sin(ph / 2.9 + 0.4)   # 20 m main repeat + finer ripples
streak *= 0.6 + 0.8 * noise(90)                        # streaks fade in and out along the flow
mid = np.clip((d - 6.0) / 25.0, 0, 1)                   # darker mid-channel
c = base[None, None] * ((0.95 + 0.10 * noise(260)) * (1 - 0.14 * mid) * (1 + 0.07 * streak))[..., None]
edge = np.clip(1 - d / 6.0, 0, 1)[..., None]
c = c * (1 - edge) + np.array([108, 104, 78]) * edge   # lighter shallows at the bank
c = np.where(m[..., None], c, base)
c = c[::-1]                       # row 0 = south (Blender v up)
c = np.roll(np.roll(c, -N // 2, 0), -N // 2, 1)   # uv 0 = scene origin
Image.fromarray(np.clip(c[::-1], 0, 255).astype(np.uint8)).save(D + 'water_col.png'); print('water_col', N, round(px, 3), int(m.sum()))
