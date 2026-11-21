# sheet of small zoom crops of the Google plan: 1 m grid, labels every 5 m; crops given as name:s:t
import sys,math
from PIL import Image,ImageDraw
im=Image.open('lplan_all_clean.png').convert('RGB');M=0.25;h=10;K=7
out=sys.argv[1];items=[a.split(':') for a in sys.argv[2:]]
W=int(2*h/M*K);S=Image.new('RGB',(W*4,W*((len(items)+3)//4)),'black')
for i,(n,s,t) in enumerate(items):
    s=float(s);t=float(t);x0=(200-(t+h))/M;y0=(s-h+200)/M
    c=im.crop((int(x0),int(y0),int(x0)+int(2*h/M),int(y0)+int(2*h/M))).resize((W,W),Image.BICUBIC);d=ImageDraw.Draw(c)
    for k in range(math.ceil(s-h),int(s+h)+1):
        y=(k-(s-h))/M*K;d.line([(0,y),(W if k%5==0 else 12,y)],fill=(255,230,0) if k%5==0 else (255,255,0),width=1)
        if k%5==0:d.text((2,y+1),'s%d'%k,fill=(255,40,255))
    for k in range(math.ceil(t-h),int(t+h)+1):
        x=((t+h)-k)/M*K;d.line([(x,0),(x,W if k%5==0 else 12)],fill=(0,230,255),width=1)
        if k%5==0:d.text((x+2,14),'t%d'%k,fill=(255,40,255))
    d.text((W-60,W-14),n,fill=(255,0,0));S.paste(c,((i%4)*W,(i//4)*W))
S.save(out,quality=88);print(S.size)
