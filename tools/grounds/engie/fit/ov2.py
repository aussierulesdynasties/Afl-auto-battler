# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import numpy as np, json, math, sys
from PIL import Image, ImageDraw
C=json.load(open('cal.json')); S,DX,DY=C['s'],C['dx'],C['dy']
E=json.load(open('edges.json'))
im=Image.open('ge/top3000.png').convert('RGB').resize((2560,1440)); d=ImageDraw.Draw(im)
def px(e,n): return 2*(640+(e-DX)/S), 2*(360-(n-DY)/S)
for key,col in (('rf',(255,255,0)),('rb',(255,60,0))):
    for b,r in E[key]:
        x,y=px(r*math.sin(math.radians(b)),r*math.cos(math.radians(b))); d.ellipse([x-3,y-3,x+3,y+3],fill=col)
extra=sys.argv[2:] 
if extra:
    F=json.load(open(extra[0]))
    for ring,col in zip(F['rings'],[(0,255,255),(0,255,0),(255,0,255),(255,255,255),(80,160,255)]):
        d.line([px(e,n) for e,n in ring]+[px(*ring[0])],fill=col,width=2)
im.save(sys.argv[1],quality=85)
