# sheet of stadium-frame crops: python spc.py z out name:u:v ... (20 m square, 0.05 m/px -> 400 px, 1 m grid)
import sys,math,numpy as np
from PIL import Image,ImageDraw
A=np.asarray(Image.open('lplan_all_clean.png').convert('RGB')).astype(float)
O=np.array([-7.12,-6.5]);import os;th=math.radians(float(os.environ.get('TH','-7.27')));U=np.array([math.cos(th),math.sin(th)]);V=np.array([-U[1],U[0]])
K=np.array([-6.94,-2.2])/38.0
z=float(sys.argv[1]);out=sys.argv[2];it=[a.split(':') for a in sys.argv[3:]];h=10;r=0.05;N=int(2*h/r)
S=Image.new('RGB',(N*4,N*((len(it)+3)//4)))
for i,(n,uc,vc) in enumerate(it):
    uc=float(uc);vc=float(vc);uu=np.arange(uc-h,uc+h,r)[:N];vv=np.arange(vc+h,vc-h,-r)[:N]
    gu,gv=np.meshgrid(uu,vv,indexing='ij');st=O+gu[...,None]*U+gv[...,None]*V+K*z
    x=(200-st[...,1])*4;y=(st[...,0]+200)*4;x0=np.clip(np.floor(x).astype(int),0,1598);y0=np.clip(np.floor(y).astype(int),0,1598)
    fx=(x-x0)[...,None];fy=(y-y0)[...,None]
    o=A[y0,x0]*(1-fx)*(1-fy)+A[y0,x0+1]*fx*(1-fy)+A[y0+1,x0]*(1-fx)*fy+A[y0+1,x0+1]*fx*fy
    im=Image.fromarray(o.astype(np.uint8));d=ImageDraw.Draw(im)
    for k in range(math.ceil(uc-h),int(uc+h)+1):
        Y=(k-(uc-h))/r;d.line([(0,Y),(N if k%5==0 else 10,Y)],fill=(255,230,0));
        if k%5==0:d.text((2,Y+1),'u%d'%k,fill=(255,40,255))
    for k in range(math.ceil(vc-h),int(vc+h)+1):
        X=((vc+h)-k)/r;d.line([(X,0),(X,N if k%5==0 else 10)],fill=(0,230,255))
        if k%5==0:d.text((X+2,12),'v%d'%k,fill=(255,40,255))
    d.text((N-70,N-14),n,fill=(255,0,0));S.paste(im,((i%4)*N,(i//4)*N))
S.save(out,quality=90);print(S.size)
