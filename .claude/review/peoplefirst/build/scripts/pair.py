import cv2,numpy as np,json,sys
from PIL import Image,ImageDraw
H=np.load(sys.argv[1]);x0,y0,x1,y1=map(int,sys.argv[3:7]);k=float(sys.argv[7])
ph=Image.open('photo.png').convert('RGB')
warp=Image.fromarray(cv2.cvtColor(cv2.warpPerspective(cv2.imread('sat.png'),H,ph.size),cv2.COLOR_BGR2RGB))
out=[]
for im in(ph,warp):
    c=im.crop((x0,y0,x1,y1)).resize((int((x1-x0)*k),int((y1-y0)*k)));d=ImageDraw.Draw(c)
    for x in range((x0//10+1)*10,x1,10):
        if x%50==0 or k>=2:d.line([((x-x0)*k,0),((x-x0)*k,c.height)],fill=(255,0,0) if x%50==0 else (255,160,160))
        if x%50==0:d.text(((x-x0)*k+2,2),str(x),fill=(255,255,0))
    for y in range((y0//10+1)*10,y1,10):
        if y%50==0 or k>=2:d.line([(0,(y-y0)*k),(c.width,(y-y0)*k)],fill=(255,0,0) if y%50==0 else (255,160,160))
        if y%50==0:d.text((2,(y-y0)*k+2),str(y),fill=(255,255,0))
    out.append(c)
W=out[0].width;S=Image.new('RGB',(W*2+6,out[0].height),'white');S.paste(out[0],(0,0));S.paste(out[1],(W+6,0));S.save(sys.argv[2])
