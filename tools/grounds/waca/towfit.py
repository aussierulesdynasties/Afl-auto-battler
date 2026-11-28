import json,math
from PIL import Image
from cam import *
a=Image.open('p92.png').convert('RGB');P=json.load(open('parts.json'))
cam=json.load(open('cam92f.json'));C=cam['p'][:3]
def grey(p):return min(p)>120 and max(p)-min(p)<45
def run(c,v):
    if not grey(a.getpixel((c,v))):
        for k in range(1,8):
            for cc in (c-k,c+k):
                if grey(a.getpixel((cc,v))):c=cc;break
            else:continue
            break
    l=c;r=c
    while l>0 and grey(a.getpixel((l-1,v))) or (l>1 and grey(a.getpixel((l-2,v)))):l-=1
    while grey(a.getpixel((r+1,v))) or grey(a.getpixel((r+2,v))):r+=1
    return l,r
r0,r1=P['tower_r']
for k,x,y,H in P['towers']:
    out=[]
    for z in (H*0.55,H*0.7,H*0.85):
        r=r0+(r1-r0)*z/H;u,v=proj(x,y,z)[:2]
        dx,dy=x-C[0],y-C[1];L=math.hypot(dx,dy);px,py=-dy/L*r,dx/L*r
        w=abs(proj(x+px,y+py,z)[0]-proj(x-px,y-py,z)[0])
        v=int(round(v));
        if v<5:continue
        l,rr=run(int(round(u)),v);pw=rr-l
        # A run more than 1.5x wider or narrower than the projected column is a different
        # structure (or the camera is off here): flag it rather than call it a match.
        bad=w<=0 or pw<=0 or not (1/1.5<=pw/w<=1.5)
        out.append('z%.0f v%d model c%.0f w%.0f | photo c%.0f w%d%s'%(z,v,u,w,(l+rr)/2,pw,' WIDTH-MISMATCH' if bad else ''))
    print(k,'; '.join(out))
