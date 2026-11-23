import json, numpy as np
from PIL import Image, ImageDraw
im = Image.open('data/accor/sat.png').convert('RGB'); W, H = im.size; cx, cy = W // 2, H // 2
T = np.array(json.load(open('data/accor/towers.json'))); keep = []
for t in T:
    if not any(np.hypot(*(t[:2] - k[:2])) < 8 for k in keep): keep.append(t)
S = 200; B = Image.new('RGB', (S * 7, S * 4), 'black'); d = ImageDraw.Draw(B)
for i, t in enumerate(keep):
    x, y = int(cx + t[0] / 0.5), int(cy - t[1] / 0.5)
    c = im.crop((x - 40, y - 40, x + 40, y + 40)).resize((S, S), Image.NEAREST)   # 40 m square
    B.paste(c, ((i % 7) * S, (i // 7) * S)); d.rectangle(((i % 7) * S + S // 2 - 4, (i // 7) * S + S // 2 - 4, (i % 7) * S + S // 2 + 4, (i // 7) * S + S // 2 + 4), outline='red')
    d.text(((i % 7) * S + 4, (i // 7) * S + 4), str(i), fill='yellow')
B.save('out/accor/towers_board.png')
