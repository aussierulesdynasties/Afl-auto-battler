# Top-down proof: the 1992 aerial (ref_full.png, frame 1182_185 crop) and the model rendered from the same 1992 camera
# (world2.py aerial, TRANSP=1) are both rectified to the ground (z=0) on one north-up grid, so roofs lean the same way in both.
# usage: python topdown.py ref_full.png render.png render_scale out.png [m_per_px]
import sys,json,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
Image.MAX_IMAGE_PIXELS=None
exec(open('cam.py').read());p=P();OFF=np.array([3800,14800])
ref,ren,rs,out=sys.argv[1],sys.argv[2],float(sys.argv[3]),sys.argv[4];R=float(sys.argv[5]) if len(sys.argv)>5 else 0.25
X0,X1,Y0,Y1=-140,125,-145,115
xs=np.arange(X0,X1,R);ys=np.arange(Y1,Y0,-R);gx,gy=np.meshgrid(xs,ys)
uv=proj(p,np.c_[gx.ravel(),gy.ravel(),np.zeros(gx.size)])-OFF
def warp(img,s):
    A=np.asarray(img).astype(float);h,w=A.shape[:2];u=np.clip(uv[:,0]*s,0,w-2);v=np.clip(uv[:,1]*s,0,h-2)
    u0=u.astype(int);v0=v.astype(int);fu=(u-u0)[:,None];fv=(v-v0)[:,None]
    c=A[v0,u0]*(1-fu)*(1-fv)+A[v0,u0+1]*fu*(1-fv)+A[v0+1,u0]*(1-fu)*fv+A[v0+1,u0+1]*fu*fv
    return c.reshape(gx.shape+(A.shape[2],))
ph=warp(Image.open(ref).convert('RGB'),1.0);md=warp(Image.open(ren).convert('RGBA'),rs)
a=md[...,3:]/255.0;mrgb=md[...,:3]
P1=ph;P2=mrgb*a+np.array([20,20,20])*(1-a);P3=ph*(1-0.5*a)+mrgb*0.5*a
al=Image.fromarray((a[...,0]*255).astype(np.uint8));edge=np.asarray(al.filter(ImageFilter.FIND_EDGES))>60
P4=ph.copy();P4[edge]=[0,255,255]
gl=Image.fromarray(np.clip(mrgb.mean(2),0,255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES);P4[(np.asarray(gl)>70)&(a[...,0]>0.5)&~edge]=[255,0,255]
try:fn=ImageFont.truetype('arial.ttf',16);fb=ImageFont.truetype('arialbd.ttf',20)
except Exception:fn=fb=ImageFont.load_default()
W,H=gx.shape[1],gx.shape[0];G=12;B=Image.new('RGB',(4*W+5*G,H+80),(18,18,18));d=ImageDraw.Draw(B)
d.text((G,8),'North Hobart Oval, 1991-92 model  |  source: Land Tasmania survey frame 1182_185, 16 Feb 1992, rectified to ground',fill=(255,255,255),font=fb)
d.text((4*W+4*G-330,12),f'north up, 10 m grid, {R} m/px',fill=(255,255,255),font=fn)
for k,(P_,l) in enumerate(((P1,'source: 1182_185, 16 Feb 1992'),(P2,'model, seen by the 1992 camera, rectified the same way'),(P3,'model 50% over source'),(P4,'source + model outline (cyan) / edges (magenta)'))):
    im=Image.fromarray(np.clip(P_,0,255).astype(np.uint8));di=ImageDraw.Draw(im)
    for x in range(X0,X1+1,10):
        if x%10==0:di.line(((x-X0)/R,0,(x-X0)/R,H),fill=(200,190,60),width=1)
    for y in range(-140,Y1+1,10):di.line((0,(Y1-y)/R,W,(Y1-y)/R),fill=(200,190,60),width=1)
    x0=G+k*(W+G);B.paste(im,(x0,70));d.text((x0,46),l,fill=(255,255,255),font=fn)
B.save(out);print(B.size)
