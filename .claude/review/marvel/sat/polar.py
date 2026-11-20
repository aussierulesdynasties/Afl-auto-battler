# unwrap the Google plan around C: rows = bearing (deg, 0 = north (-s), 90 = east (-t)), cols = radius 40..170 m at 0.25 m
import numpy as np,sys
from PIL import Image,ImageDraw
A=np.asarray(Image.open('lplan_all_clean.png').convert('RGB')).astype(float)
C=np.array([-14.06,-8.7]);R=np.arange(40,170,0.25);B=np.arange(0,360,0.5)
b=np.radians(B)[:,None];ds=-np.cos(b);dt=-np.sin(b)
s=C[0]+R[None]*ds;t=C[1]+R[None]*dt;x=(200-t)*4;y=(s+200)*4
o=A[np.clip(y.astype(int),0,1599),np.clip(x.astype(int),0,1599)].astype(np.uint8)
im=Image.fromarray(o).resize((len(R)*2,len(B)*2),Image.NEAREST);d=ImageDraw.Draw(im)
for r in range(40,171,10):X=(r-40)*8;d.line([(X,0),(X,im.height)],fill=(255,0,255) if r%50==0 else (255,255,0));d.text((X+2,2),str(r),fill=(255,0,0))
for a in range(0,360,10):Y=a*4;d.line([(0,Y),(30,Y)],fill=(0,255,255));d.text((32,Y-6),str(a),fill=(0,255,255))
im.save('polar.png');print(im.size)
