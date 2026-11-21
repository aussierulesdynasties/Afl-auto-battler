import json,math,sys
from PIL import Image,ImageDraw
D=json.load(open('model/mcg.json'))
im=Image.open('sat/esri_025.png').convert('RGB');d=ImageDraw.Draw(im)
def P(b,r): return ((r*math.sin(math.radians(b))+260)*4,(260-r*math.cos(math.radians(b)))*4)
for key,col in (('plaza',(255,0,0)),('gravel',(0,255,255))):
    t=D[key];pts=[P(b,r) for b,r in t]+[P(t[0][0]+360,t[0][1])]
    d.line(pts,fill=col,width=2)
for b in range(0,360,5):
    d.line([P(b,120),P(b,230)],fill=(255,255,0),width=1)
    x,y=P(b,128);d.rectangle([x-12,y-6,x+12,y+6],fill=(0,0,0));d.text((x-10,y-5),str(b),fill=(255,255,0))
for r in range(130,231,10):
    d.line([P(b/4,r) for b in range(0,1441)],fill=(255,255,255) if r%50 else (255,128,0),width=1)
q=sys.argv[1]
box={'S':(500,1400,1540,2080),'W':(0,500,800,1500),'N':(500,0,1540,700),'E':(1300,500,2080,1500)}[q]
im.crop(box).save('work/plz_%s.png'%q)
