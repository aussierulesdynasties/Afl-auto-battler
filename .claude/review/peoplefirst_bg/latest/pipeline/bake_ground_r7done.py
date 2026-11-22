"""Bake tex/ground_detail.png (one tile = 4 m, x1.21 lift) into the scene's ground.png -> data/<name>/prep/ground_baked.png.
Usage: python -E bake_ground.py mcg [px]. Multiplies in linear light like Blender did, re-encodes sRGB. Prints grey std."""
import os, sys, json
import numpy as np
from PIL import Image, ImageFilter
Image.MAX_IMAGE_PIXELS = None
H = os.path.dirname(os.path.abspath(__file__)); name = sys.argv[1]; S = int(sys.argv[2]) if len(sys.argv) > 2 else 8192
D = os.path.join(H, 'data', name, 'prep'); NE = json.load(open(os.path.join(D, 'meta.json')))['near']
def dec(a): a = a / 255.0; return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def enc(v): v = np.clip(v, 0, 1); return 255 * np.where(v <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055)
g = Image.open(os.path.join(D, 'ground.png')).convert('RGB').resize((S, S), Image.BICUBIC)
tiles = 2 * NE / 4.0; ppt = S / tiles   # output px per detail tile
_pg = np.asarray(Image.open(os.path.join(H, 'tex', 'pf_grass.png')).convert('RGB'), np.float32); _l = _pg @ np.array([0.299, 0.587, 0.114])
_st = _l.mean(0); _st = np.asarray(Image.fromarray((_st / _st.max() * 255).astype(np.uint8)[None]).resize((512, 1), Image.BILINEAR), np.float32)[0]; _st /= _st.mean(); _st = 1 + 0.0 * (_st - 1)   # People First mowing stripes only (column profile: seamless)
_od = np.asarray(Image.open(os.path.join(H, 'tex', 'ground_detail.png')).convert('RGB'), np.float32)   # seamless clumps tile
det = Image.fromarray(np.clip(_od * _st[None, :, None], 0, 255).astype(np.uint8)); DS = det.size[0]
# pre-filter the tile (wrapped) to the output footprint, as texture filtering would
sig = max(0.0, DS / ppt / 2); big = Image.fromarray(np.tile(np.asarray(det), (3, 3, 1)))
det = np.asarray(big.filter(ImageFilter.GaussianBlur(sig)), np.float32)[DS:2 * DS, DS:2 * DS]
dl = dec(det)
c = (np.arange(S) + 0.5) / S * tiles
fx = (c % 1.0) * DS - 0.5                      # u -> column
fy = ((1.0 - (c % 1.0)) * DS - 0.5)            # rows run down: v = 1 - row
i0 = np.floor(fx).astype(int); ax = (fx - i0)[None, :, None]
out = np.empty((S, S, 3), np.uint8); ga = np.asarray(g)
for r0 in range(0, S, 512):
    rr = np.arange(r0, min(S, r0 + 512)); j0 = np.floor(fy[rr]).astype(int); ay = (fy[rr] - j0)[:, None, None]
    J0, J1 = j0 % DS, (j0 + 1) % DS; I0, I1 = i0 % DS, (i0 + 1) % DS
    d = (dl[J0][:, I0] * (1 - ax) + dl[J0][:, I1] * ax) * (1 - ay) + (dl[J1][:, I0] * (1 - ax) + dl[J1][:, I1] * ax) * ay
    out[rr] = np.round(enc(dec(ga[rr].astype(np.float32)) * d * 1.21)).astype(np.uint8)
# grass: mowing stripes (9 m bands, direction per 160 m block) and wear toward straw by 50 m noise
m_ = 2 * NE / S; R_ = np.random.default_rng(7)
import math
from PIL import ImageDraw
_sp = json.load(open(os.path.join(H, 'spec', name + '.json'))); _KX = 111320 * math.cos(math.radians(_sp['lat'])); _KY = 110540
PM = Image.new('L', (S, S), 0); _pd = ImageDraw.Draw(PM); PL = Image.new('L', (S, S), 0); _pl = ImageDraw.Draw(PL); PA = [0.0]
_js = json.load(open(os.path.join(H, 'data', name, 'osm.json'))); _js = _js['elements'] if isinstance(_js, dict) else _js
for el in _js:
    t = el.get('tags', {})
    if el.get('type') != 'way' or t.get('leisure') != 'pitch' or not el.get('geometry'): continue
    if t.get('surface', 'grass') not in ('grass', 'unknown') or any(k in t.get('sport', '') for k in ('tennis', 'basketball', 'netball', 'skate')): continue
    pts = [(((p['lon'] - _sp['lon']) * _KX + NE) / m_, (NE - (p['lat'] - _sp['lat']) * _KY) / m_) for p in el['geometry'] if p]
    if len(pts) > 2:
        _q = np.array(pts) * m_; _q = _q - _q.mean(0); _w, _v = np.linalg.eigh(_q.T @ _q); _ax = _v[:, -1]   # long axis of the pitch
        PA.append(math.atan2(-_ax[1], _ax[0])); _pd.polygon(pts, fill=255); _pl.polygon(pts, fill=min(255, len(PA) - 1))
PL = np.asarray(PL); PA = np.array(PA); PM = np.asarray(PM.filter(ImageFilter.GaussianBlur(1.0 / m_)), np.float32) / 255; print('pitch px', int((PM > 0.5).sum()))
wn = np.asarray(Image.fromarray((R_.random((int(2 * NE / 50) + 2,) * 2) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32) / 255
bd = R_.integers(0, 4, (int(2 * NE / 160) + 2,) * 2); straw = np.array([186, 172, 120], np.float32)
xs = -NE + (np.arange(S) + 0.5) * m_
def _nz(cell, seed, ax=None):   # value noise at a cell size in metres (ax: (rows, cols) cell sizes for streaks)
    r = np.random.default_rng(seed); cy, cx = (cell, cell) if ax is None else ax
    return np.asarray(Image.fromarray((r.random((int(2 * NE / cy) + 2, int(2 * NE / cx) + 2)) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32) / 255
_o0 = out.astype(np.int16); GM = ((_o0[..., 1] > _o0[..., 0] * 1.08) & (_o0[..., 1] > _o0[..., 2] * 1.15)); del _o0
GB = np.asarray(Image.fromarray((GM * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5 / m_)), np.float32) / 255
N80, N300, NDMP, NTF = _nz(80, 21), _nz(300, 22), _nz(22, 23), _nz(1.6, 24)
for r0 in range(0, S, 512):
    rr = np.arange(r0, min(S, r0 + 512)); ys = NE - (rr + 0.5) * m_
    X_, Y_ = np.meshgrid(xs, ys); o = out[rr].astype(np.float32)
    gm = (o[..., 1] > o[..., 0] * 1.08) & (o[..., 1] > o[..., 2] * 1.15)
    ang = bd[((Y_ + NE) // 160).astype(int), ((X_ + NE) // 160).astype(int)] * (np.pi / 4)
    ang = np.where(PL[rr] > 0, PA[PL[rr]], ang)   # bands run along each pitch's long axis
    sv = X_ * np.cos(ang) + Y_ * np.sin(ang)
    f = 1 + 0.05 * np.tanh(3 * np.sin(2 * np.pi * sv / 12.0)) * PM[rr]   # mown bands only on sports pitches
    w = 0.22 * np.clip((wn[rr] - 0.55) / 0.45, 0, 1)
    g2 = (o * f[..., None]) * (1 - w[..., None]) + straw * w[..., None]
    tone = 1 + 0.16 * (N80[rr] - 0.5) + 0.22 * (N300[rr] - 0.5) + 0.12 * (NTF[rr] - 0.5)   # broad and tuft variation
    damp = np.clip((NDMP[rr] - 0.66) / 0.14, 0, 1) * (1 - PM[rr])                           # darker damp blotches
    edg = 1 - 0.22 * np.clip((0.97 - GB[rr]) / 0.45, 0, 1)                                    # darker along paths, water, kerbs
    g2 = g2 * (tone * edg)[..., None]; g2 = g2 * (1 - 0.3 * damp[..., None]) + np.array([46, 70, 48], np.float32) * 0.3 * damp[..., None]
    out[rr] = np.where(gm[..., None], np.clip(g2, 0, 255), o).astype(np.uint8)
o3 = out.astype(np.int16); wm = (o3[..., 2] > o3[..., 0] + 20) & (o3[..., 2] + 6 > o3[..., 1])
WM = Image.fromarray((wm * 255).astype(np.uint8))
deep = np.asarray(WM.filter(ImageFilter.GaussianBlur(14 / m_)), np.float32) / 255     # ~1 in mid channel, ~0.5 at the bank
edge = np.asarray(WM.filter(ImageFilter.GaussianBlur(1.5 / m_)), np.float32) / 255
tn = np.asarray(Image.fromarray((R_.random((int(2 * NE / 30) + 2,) * 2) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32) / 255
RIP = _nz(0, 31, (3.0, 26.0)); RIP2 = _nz(0, 32, (7.0, 60.0)); GL = _nz(0, 33, (1.2, 7.0)); GLB = _nz(140, 34)
shallow = np.array([96, 120, 118], np.float32); chan = np.array([40, 66, 82], np.float32); mud = np.array([150, 140, 112], np.float32)
for r0 in range(0, S, 512):
    rr = slice(r0, min(S, r0 + 512)); t = np.clip((deep[rr] - 0.5) / 0.45, 0, 1)[..., None]
    w = shallow * (1 - t) + chan * t; w = w * (0.92 + 0.16 * tn[rr][..., None])
    w = w * (1 + 0.20 * (RIP[rr] - 0.5) + 0.14 * (RIP2[rr] - 0.5))[..., None]                 # wind ripple streaks
    w = w * (1 - 0.22 * np.clip((0.68 - deep[rr]) / 0.18, 0, 1))[..., None]                    # darker band along the shore
    gl = np.clip((GL[rr] - 0.80) / 0.10, 0, 1) * np.clip((GLB[rr] - 0.35) / 0.3, 0, 1) * t[..., 0]   # sun glint flecks in patches
    w = w * (1 - 0.8 * gl[..., None]) + np.array([214, 224, 226], np.float32) * 0.8 * gl[..., None]
    w = np.where(((edge[rr] < 0.75) & wm[rr])[..., None], mud * 0.6 + w * 0.4, w)
    sh = (~wm[rr]) & (edge[rr] > 0.06)                                                  # wet bank just outside the water line
    o = out[rr].astype(np.float32); o = np.where(sh[..., None], o * 0.5 + mud * 0.5, o)
    out[rr] = np.where(wm[rr][..., None], w, o).clip(0, 255).astype(np.uint8)
p = os.path.join(D, 'ground_baked.png'); Image.fromarray(out).save(p, optimize=False)
gr = out[::4, ::4].astype(np.float32) @ np.array([0.299, 0.587, 0.114])
print(p, S, 'px, %.3f m/px' % (2 * NE / S), 'grey std %.1f' % gr.std(), 'MB %.1f' % (os.path.getsize(p) / 1e6))
