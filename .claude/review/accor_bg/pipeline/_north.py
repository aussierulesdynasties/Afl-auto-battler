from PIL import Image
im = Image.open('data/accor/sat.png').convert('RGB'); W, H = im.size; cx, cy = W // 2, H // 2
x0, x1, y0, y1 = -330, 30, 820, 440   # metres
im.crop((int(cx + x0 / .5), int(cy - y0 / .5), int(cx + x1 / .5), int(cy - y1 / .5))).save('out/accor/north.png')
