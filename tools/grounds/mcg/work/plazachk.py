import json,math,sys
from PIL import Image,ImageDraw
D=json.load(open('model/mcg.json'))
im=Image.open('sat/esri_025.png').convert('RGB');d=ImageDraw.Draw(im)
def P(b,r): return ((r*math.sin(math.radians(b))+260)*4,(260-r*math.cos(math.radians(b)))*4)
for key,col in (('plaza',(255,0,0)),('gravel',(0,255,255))):
    t=D[key];pts=[P(b,r) for b,r in t]+[P(t[0][0]+360,t[0][1])]
    d.line(pts,fill=col,width=3)
for b in range(0,360,10):
    d.line([P(b,120),P(b,230)],fill=(255,255,0),width=1);d.text(P(b,235),str(b),fill=(255,255,0))
for r in (140,160,180,200,220):
    d.line([P(b/2,r) for b in range(0,721)],fill=(255,255,255),width=1)
im.crop((80,80,2000,2000)).resize((1200,1200)).save('work/plazachk.png')
