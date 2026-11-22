# Zoomed aerial section with a labelled 5 m grid for hand-tracing sail corners. args: name x0 x1 y0 y1
import sys
from PIL import Image, ImageDraw
n, x0, x1, y0, y1 = sys.argv[1], *map(float, sys.argv[2:6]); Z = 8
im = Image.open('data/riverway/sat.png').convert('RGB').crop((int((x0+1600)*2), int((1600-y1)*2), int((x1+1600)*2), int((1600-y0)*2)))
im = im.resize((im.width*Z, im.height*Z), Image.LANCZOS); d = ImageDraw.Draw(im); k = 2*Z
x = x0
while x <= x1:
    X = (x-x0)*k; d.line([(X,0),(X,im.height)], fill=(255,255,0) if x%10==0 else (0,200,200)); 
    if x%10==0: d.text((X+2,2), str(int(x)), fill=(255,255,0))
    x += 5
y = y0
while y <= y1:
    Y = (y1-y)*k; d.line([(0,Y),(im.width,Y)], fill=(255,255,0) if y%10==0 else (0,200,200))
    if y%10==0: d.text((2,Y+2), str(int(y)), fill=(255,255,0))
    y += 5
im.save(f'out/riverway/chk/tr_{n}.png'); print(n, im.size)
