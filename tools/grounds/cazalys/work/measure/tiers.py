import json,sys,math,numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,'of'); import zline as Z, solve as S
sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/cazalys/work'); import fence_ge as fg
G=json.load(open('/home/user/Afl-auto-battler/tools/grounds/cazalys/model/cazalys.json'))['grandstand']
E=[-1.2135,-3.69,75.22,87.49,28.87]
def pol(b,r): b=math.radians(b); return r*math.sin(b), r*math.cos(b)
def foff(b,d):
    # radius along bearing b of the curve offset d outward from the fence ellipse
    lo,hi=10,200
    for _ in range(50):
        m=(lo+hi)/2; x,y=pol(b,m); s=fg.dist(E,np.array([[x,y]]))[0] if hasattr(fg,'dist') else None
        if s<d: lo=m
        else: hi=m
    return (lo+hi)/2
def it(tab,b): t=np.array(tab,float); return float(np.interp(b,t[:,0],t[:,1]))
bs=np.arange(G['b0'],G['b1']+0.01,0.5)
zl0,zl1=G['z_lower']; zu0,zu1=G['z_upper']
LINES={'lower front top (z%.1f)'%zl0:[(foff(b,G['front']),zl0) for b in bs],
 'walkway (z%.1f)'%zl1:[(it(G['upper_front'],b)-1.6,zl1) for b in bs],
 'upper front top (z%.1f)'%zu0:[(it(G['upper_front'],b),zu0) for b in bs],
 'upper back (z%.1f)'%zu1:[(it(G['upper_back'],b),zu1) for b in bs]}
cols=[(255,0,0),(255,255,0),(0,255,255),(255,0,255)]
for view in sys.argv[1:]:
    p=np.array(Z.SOL[view]['p']); im=Image.open(f'of/ge/{view}.png').convert('RGB'); d=ImageDraw.Draw(im)
    for (k,L),c in zip(LINES.items(),cols):
        P=np.array([[*pol(b,r),z] for b,(r,z) in zip(bs,L)]); uv,_=S.proj(p,P); d.line([tuple(q) for q in uv],fill=c,width=1)
    im.save(f'rf/tiers_{view}.png')
print(list(LINES))
