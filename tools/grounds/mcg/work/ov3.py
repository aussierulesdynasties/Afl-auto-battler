# python work/ov3.py view... : photo | render | 50% blend, stacked, half size -> work/ov3_<view>.png
import sys
from PIL import Image
for v in sys.argv[1:]:
    a=Image.open(f'ge/{v}.png').convert('RGB');b=Image.open(f'rr/{v}.png').convert('RGB').resize(a.size)
    c=Image.blend(a,b,0.5);w,h=a.width//2,(a.height-84-30)//2
    o=Image.new('RGB',(w,3*h+8))
    for k,im in enumerate((a,b,c)):o.paste(im.crop((0,84,a.width,a.height-30)).resize((w,h)),(0,k*(h+4)))
    o.save(f'work/ov3_{v}.png')
