# ovtop.py style: model (straight down, optional camera lean) over the straight-down source, 0.25 m/px, north up, 10 m grid.
# args: src.png model.png outdir [dx_px dy_px rot_deg cx cy]  -> t_src, t_model, t_blend, t_on, t_on_NW/NE/SW/SE
import sys,numpy as np,cv2,os
from PIL import Image,ImageDraw,ImageFilter
src,mod,od=sys.argv[1:4];T=[float(v) for v in sys.argv[4:9]] if len(sys.argv)>8 else None
A=Image.open(src).convert('RGB');M=Image.open(mod).convert('RGBA');n=A.size[0];H=n/2*0.25
if T:
    dx,dy,rot,cx,cy=T;R=cv2.getRotationMatrix2D((cx,cy),-rot,1.0);R[:,2]+=[dx,dy]
    M=Image.fromarray(cv2.warpAffine(np.asarray(M),R,(n,n),flags=cv2.INTER_NEAREST))
a=np.asarray(M)[...,3]>10
g=np.asarray(M.convert('L')).astype(float);ed=(np.abs(np.diff(g,axis=0,prepend=0))+np.abs(np.diff(g,axis=1,prepend=0)))>25
sil=a&~(np.asarray(Image.fromarray(a.astype(np.uint8)*255).filter(ImageFilter.MinFilter(5)))>0)
on=np.asarray(A).copy();on[ed&a]=(255,40,200);on[sil]=(0,255,255)
bl=Image.blend(A,Image.alpha_composite(A.convert('RGBA'),M).convert('RGB'),0.5)
def grid(im):
    d=ImageDraw.Draw(im)
    for k in range(-int(H)//10*10,int(H)+1,10):
        X=(k+H)*4;Y=(H-k)*4;col=(255,230,0) if k%50==0 else (120,110,0)
        d.line([(0,Y),(n,Y)],fill=col);d.line([(X,0),(X,n)],fill=col)
        if k%50==0:d.text((2,Y+1),'N%d'%k,fill=(255,255,255));d.text((X+2,2),'E%d'%k,fill=(255,255,255))
    return im
os.makedirs(od,exist_ok=True)
O=grid(Image.fromarray(on));O.save(od+'/t_on.jpg',quality=92);grid(bl).save(od+'/t_blend.jpg',quality=92);grid(A.copy()).save(od+'/t_src.jpg',quality=92)
Mo=Image.new('RGB',M.size,(40,40,40));Mo.paste(M,(0,0),M);grid(Mo).save(od+'/t_model.jpg',quality=92)
M.save(od+'/model_fitted.png')
ys,xs=np.nonzero(a);x0,x1,y0,y1=xs.min()-40,xs.max()+40,ys.min()-40,ys.max()+40;xm,ym=(x0+x1)//2,(y0+y1)//2
for nm,(a0,b0,a1,b1) in {'NW':(x0,y0,xm,ym),'NE':(xm,y0,x1,ym),'SW':(x0,ym,xm,y1),'SE':(xm,ym,x1,y1)}.items():
    O.crop((a0,b0,a1,b1)).resize(((a1-a0)*2,(b1-b0)*2),Image.LANCZOS).save(od+'/t_on_%s.jpg'%nm,quality=90)
print('bbox px',x0,y0,x1,y1)
