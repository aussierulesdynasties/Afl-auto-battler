# zoom of sat_uv.png (and optionally r_top.png overlay) with a 1 m / 5 m grid: python zoomuv.py u0 u1 v0 v1 scale out [model]
import sys,numpy as np
from PIL import Image,ImageDraw
u0,u1,v0,v1,sc=map(float,sys.argv[1:6]);out=sys.argv[6];mode=sys.argv[7] if len(sys.argv)>7 else 'sat'
A=Image.open('sat_uv.png').convert('RGB')
if mode!='sat':
    M=Image.open('r_top.png').convert('RGBA')
    if mode=='model':B=Image.new('RGB',M.size,(40,40,40));B.paste(M,(0,0),M);A=B
    elif mode=='edge':
        from PIL import ImageFilter
        a=np.asarray(M)[:,:,3]>0;L=np.asarray(M.convert('L')).astype(float)
        ed=np.abs(np.asarray(Image.fromarray(L.astype(np.uint8)).filter(ImageFilter.FIND_EDGES))).astype(float)>25
        sil=a&~(np.asarray(Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)))>0)
        X=np.asarray(A).copy();X[ed&a]=(255,0,255);X[sil]=(0,255,255);A=Image.fromarray(X)
    else:A=Image.blend(A,Image.alpha_composite(A.convert('RGBA'),M).convert('RGB'),0.5)
box=(int((150-v1)*4),int((u0+150)*4),int((150-v0)*4),int((u1+150)*4))
im=A.crop(box);im=im.resize((int(im.width*sc/4),int(im.height*sc/4)),Image.LANCZOS);d=ImageDraw.Draw(im)
for k in range(int(np.ceil(u0)),int(u1)+1):
    Y=(k-u0)*sc
    if k%5==0:d.line([(0,Y),(im.width,Y)],fill=(255,230,0) if k%10==0 else (150,140,0));d.text((2,Y+1),'u%d'%k,fill=(255,40,255))
for k in range(int(np.ceil(v0)),int(v1)+1):
    X=(v1-k)*sc
    if k%5==0:d.line([(X,0),(X,im.height)],fill=(0,230,255) if k%10==0 else (0,130,150));d.text((X+2,2),'v%d'%k,fill=(255,40,255))
im.save(out,quality=92);print(im.size)
