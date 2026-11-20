import sys;from cam import *
from PIL import Image,ImageDraw
key=sys.argv[1];zs=[float(z) for z in sys.argv[2].split(',')];x0,y0,x1,y1=map(int,sys.argv[3:7]);k=float(sys.argv[7])
im=Image.open('photo.png').convert('RGB').crop((x0,y0,x1,y1));im=im.resize((int((x1-x0)*k),int((y1-y0)*k)));d=ImageDraw.Draw(im)
cols=[(255,0,0),(255,128,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255),(255,255,255)]
for i,z in enumerate(zs):
    pts=G[key];Y=(proj([(x,y,z) for x,y in pts])-[x0,y0])*k;d.line([tuple(a) for a in Y],fill=cols[i%8],width=2)
    for j,a in enumerate(Y):
        if i==0:d.text(tuple(a),str(j),fill=(255,255,255))
    d.text((5,5+14*i),f'z={z}',fill=cols[i%8])
for x in range((x0//50+1)*50,x1,50):d.text(((x-x0)*k,y1*0+ (y1-y0)*k-14),str(x),fill=(255,255,255))
for y in range((y0//50+1)*50,y1,50):d.text(((x1-x0)*k-30,(y-y0)*k),str(y),fill=(255,255,255))
im.save(sys.argv[8])
