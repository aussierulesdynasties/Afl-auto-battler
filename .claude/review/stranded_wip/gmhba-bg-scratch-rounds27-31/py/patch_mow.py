import sys
p = sys.argv[1]; t = open(p, newline='').read()
a = "# hand-made grain: per-pixel value noise, never photo pixels\n"
assert a in t and 'mowing stripes' not in t
b = """# mowing stripes and wear on grass (hand-made, aerial used only to place them)
_a = np.asarray(img).astype(np.float32); _L = np.array(PAL['lawn'], np.float32)
_g = (np.abs(_a - _L).max(-1) < 34).astype(np.float32)   # lawn-coloured pixels only
_st = Image.new('L', (N, N), 128); _sd = ImageDraw.Draw(_st)
for el in js:   # every OSM pitch: 8 m stripes along its long axis, clipped to the pitch
    tg = el.get('tags', {})
    if el['type'] != 'way' or tg.get('leisure') != 'pitch' or 'geometry' not in el: continue
    pts = ring(el)
    if len(pts) < 4: continue
    cx, cy, ang, L_, W_ = _obox(pts[:-1] if pts[0] == pts[-1] else pts)
    ux, uy = math.cos(ang), math.sin(ang); wx, wy = -uy, ux
    pm = Image.new('L', (N, N), 0); ImageDraw.Draw(pm).polygon(P(pts), fill=255)
    sm = Image.new('L', (N, N), 128); smd = ImageDraw.Draw(sm); k = 0; off = -W_ / 2 - 8
    while off < W_ / 2 + 8:
        q = [(cx + ux * s_ + wx * o_, cy + uy * s_ + wy * o_) for s_, o_ in ((-L_, off), (L_, off), (L_, off + 8), (-L_, off + 8))]
        smd.polygon(P(q), fill=146 if k % 2 else 110); k += 1; off += 8
    _st.paste(sm, (0, 0), pm)
_s = (np.asarray(_st).astype(np.float32) - 128) / 128 * 0.5   # +-7 %
_w = np.asarray(Image.fromarray((rng.random((N // 53 + 1, N // 53 + 1)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)).astype(np.float32) / 255
_w = np.clip((_w - 0.62) / 0.3, 0, 1) * 0.45   # patchy dry wear, ~40 m blobs, up to 45 % toward dry grass
_dry = np.array(PAL.get('lawn_dry', [150, 140, 92]), np.float32)
for (cx, cy, ang, L_, W_), _q in OV:   # oval wear: centre square and both goal squares
    for s_, rx, ry in ((0, 28, 22), (-L_ / 2 + 9, 12, 9), (L_ / 2 - 9, 12, 9)):
        ex, ey = cx + math.cos(ang) * s_, cy + math.sin(ang) * s_
        em = Image.new('L', (N, N), 0); ImageDraw.Draw(em).ellipse(P([(ex - rx, ey + ry), (ex + rx, ey - ry)]), fill=255)
        em = np.asarray(em.filter(ImageFilter.GaussianBlur(6 / PX))).astype(np.float32) / 255; _w = np.maximum(_w, em * 0.55)
_a = _a * (1 - _g * _w)[..., None] + _dry[None, None] * (_g * _w)[..., None]
_a *= (1 + 0.14 * _s * _g)[..., None]
img = Image.fromarray(np.clip(_a, 0, 255).astype(np.uint8))
"""
open(p, 'w', newline='').write(t.replace(a, b + a))
print('ok')
