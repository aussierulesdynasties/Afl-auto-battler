# C6 texture look pass (2026-11-20): seats, grey facade and brick redrawn by hand to match their photo-03 crops
# (tex_vs_photo board). No photo pixels: flat colours read off the photo as medians, drawn as procedural patterns.
import numpy as np
from PIL import Image, ImageFilter
rng = np.random.default_rng(31); S = 512; x = np.arange(S); y = np.arange(S)
def save(a, n): Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save('tex/' + n + '.png')
def noise(blur=1):
    n = rng.normal(0, 1, (S, S)); return np.array(Image.fromarray(((n * 20 + 128).clip(0, 255)).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur)), float) - 128
# empty seats: dark bottle-green plastic (photo median 60,69,65), darker riser shadow, grey step, pale aisle stair at tile edge
s = np.full((512, 1024, 3), [92, 96, 94.]); row = (y % 102)[:, None].repeat(1024, 1)   # 8 m wide x 4 m deep tile
s[(row > 10) & (row < 66)] = [58, 74, 66]; s[(row >= 66) & (row < 78)] = [36, 46, 42]
s[:, 0:40] = [178, 180, 174]; s[:, 40:44] = [96, 100, 98]                       # one aisle stair per 8 m
nz = np.array(Image.fromarray((rng.normal(0, 1, (512, 1024)) * 20 + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), float) - 128
s += nz[..., None] * 0.25; save(s, 'seatsg')
# grey precast cores and bays: grey-green panels (photo 166,165,152), faint 2 m panel joints, thin shadow line each storey
f = np.full((S, S, 3), [166, 166, 153.]); f[:, (x % 128) < 3] = [140, 141, 130]; f[(y % 128) < 3] = [128, 129, 120]
f[(y % 128 > 3) & (y % 128 < 8)] = [182, 182, 170]; f += noise(1.2)[..., None] * 0.18; save(f, 'facc')
# red brick colonnade/end block (photo 199,129,100): brick body, white concrete floor band, a ribbon of dark windows in white frames
b = np.full((S, S, 3), [190, 112, 84.]); c = (y // 10) % 2; off = np.where(c[:, None] == 1, 15, 0)
b[(y % 10) < 1] = [205, 170, 150]; b[((x[None, :] + off) % 30) < 1] = [205, 170, 150]
st = y % 512; b[st < 56] = [226, 224, 216]                                          # floor slab band
wx = (x > 150) & (x < 350); b[np.outer((st > 200) & (st < 330), wx)] = [232, 230, 222]   # one framed window per 4 m bay
b[np.outer((st > 212) & (st < 318), (x > 162) & (x < 338) & ((x - 250) ** 2 > 16))] = [52, 58, 66]
b += noise(0.6)[..., None] * 0.3; save(b, 'brickr')
# open arcade under the colonnade (one 4 m bay per tile, 3.5 m tall): white pier, dark shaded bay, pale soffit at the top
a = np.full((S, S, 3), [40, 36, 36.]); a[:, (x % 512) < 72] = [228, 222, 210]; a[:, ((x % 512) >= 72) & ((x % 512) < 80)] = [150, 140, 130]
a[0:130] = [226, 222, 214]; a[130:140] = [120, 112, 104]
a += noise(1)[..., None] * 0.25; save(a, 'arcade')
print('ok')
