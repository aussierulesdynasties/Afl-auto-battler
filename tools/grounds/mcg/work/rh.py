import sys,json,numpy as np;sys.path.insert(0,'work');import tri,earthcam as E
from PIL import Image
D=json.load(open('model/mcg.json'));ri=np.array(D['roof_inner'],float)
def RI(b):return np.interp(b%360,np.r_[ri[:,0],ri[0,0]+360],np.r_[ri[:,1],ri[0,1]])
C=json.load(open('work/cams.json'));ims={}
out={}
for b in range(0,360,5):
    res=[]
    for v in [k for k in C if k[0] in 'lo']:
        H=C[v][4];nb=(H+180)%360;dd=abs((b-nb+180)%360-180)
        if dd>35:continue
        c=tri.camv(v)
        if v not in ims:ims[v]=np.asarray(Image.open(f'ge/{v}.png').convert('RGB')).astype(int)
        im=ims[v];r=RI(b);x,y=r*np.sin(np.radians(b)),r*np.cos(np.radians(b))
        zs=np.arange(20,50,0.25);g=[]
        for z in zs:
            u,w=E.proj(c,[x,y,z]);u,w=int(round(u)),int(round(w))
            if not(0<=u<1920 and 90<=w<1045):g.append(-1);continue
            p=im[w-1:w+2,u-1:u+2].reshape(-1,3).mean(0);g.append(1 if (p[1]>p[0]+8 and p[1]>p[2]+12) else 0)
        g=np.array(g)
        # first z above which >=6 of next 8 are green
        for i in range(len(g)-8):
            if g[i]==1 and (g[i:i+8]==1).sum()>=6 and (g[max(0,i-8):i]==0).sum()>=5:res.append((v,float(zs[i])));break
    out[b]=res;print(b,round(RI(b),1),res)
