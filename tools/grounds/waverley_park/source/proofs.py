from PIL import Image, ImageDraw
import os
O = 'out/proof/'
os.makedirs(O, exist_ok=True)
W, H = 1023, 576
ref = Image.open('ref.jpg').convert('RGB')
r = Image.open('out/render.png').convert('RGBA').resize((W, H), Image.LANCZOS)
grey = Image.new('RGBA', (W, H), (198, 214, 230, 255))   # pale sky, so grey roofs read against it
grey.alpha_composite(r)
ren = grey.convert('RGB')
ov = Image.blend(ref, ren, 0.5)
board = Image.new('RGB', (W * 3 + 20, H + 30), (20, 20, 20))
d = ImageDraw.Draw(board)
for i, (im, t) in enumerate(((ref, 'photo (Austadiums waverley-park-5, 1996)'), (ren, 'model, matched camera'), (ov, '50% overlay'))):
    board.paste(im, (i * (W + 10), 30))
    d.text((i * (W + 10) + 6, 8), t, fill=(255, 255, 255))
board.save(O + 'waverley_photo_render_overlay.png')
ren.save(O + 'waverley_render_1023.png')
ov.save(O + 'waverley_overlay50_1023.png')
PARTS = {
    'members_stand': (260, 40, 660, 200),
    'near_side': (250, 380, 800, 576),
    'left_end_tower_D': (0, 200, 330, 520),
    'right_end_tower_C_shed': (760, 120, 1023, 440),
    'far_right': (620, 40, 1000, 200),
    'far_left': (0, 40, 330, 230),
}
for n, b in PARTS.items():
    w, h = b[2] - b[0], b[3] - b[1]
    s = 900 / w
    sz = (int(w * s), int(h * s))
    bd = Image.new('RGB', (sz[0], sz[1] * 3 + 60), (20, 20, 20))
    dd = ImageDraw.Draw(bd)
    for i, (im, t) in enumerate(((ref, 'photo'), (ren, 'model'), (ov, '50% overlay'))):
        bd.paste(im.crop(b).resize(sz, Image.LANCZOS), (0, i * (sz[1] + 20) + 20))
        dd.text((6, i * (sz[1] + 20) + 4), f'{n}: {t}', fill=(255, 255, 255))
    bd.save(O + f'part_{n}.png')
print('ok')
