import json,math,sys,numpy as np
from PIL import Image,ImageDraw
from scipy.optimize import least_squares
sys.path.insert(0,'of'); import solve as S
F=S.F
NV={v['name']:v for v in json.load(open('st/v.json'))}; OBS=json.load(open('st/obs.json'))
def nproj(v,x,y,z):
    h=math.radians(v['h']); s=F/(v['d']+v['at'][2]-z); dx,dy=x-v['at'][0],y-v['at'][1]
    return np.array([640+(dx*math.cos(h)-dy*math.sin(h))*s, 360-(dx*math.sin(h)+dy*math.cos(h))*s])
def xy_at(c,z):
    o=OBS[c]; f=lambda p: np.concatenate([nproj(NV[n],p[0],p[1],z)-np.array(o[n]) for n in o])
    r=least_squares(f,[-80,-48]); return r.x
SOL=json.load(open('of/solved.json'))
if __name__=='__main__':
    view=sys.argv[1]; p=np.array(SOL[view]['p']); im=Image.open(f'of/ge/{view}.png').convert('RGB')
    x0,y0,x1,y1=400,80,920,320; sc=3
    im=im.crop((x0,y0,x1,y1)).resize(((x1-x0)*sc,(y1-y0)*sc),Image.LANCZOS); d=ImageDraw.Draw(im)
    cols={'FL':(255,0,0),'FK':(255,128,0),'FR':(255,255,0),'RR':(0,255,0),'RK':(0,255,255),'B2':(0,128,255),'B1':(255,0,255),'LR':(255,255,255)}
    for c in OBS:
        pts=[]
        for z in np.arange(4,16.01,1):
            X,Y=xy_at(c,z); uv,_=S.proj(p,np.array([[X,Y,z]])); pts.append(((uv[0,0]-x0)*sc,(uv[0,1]-y0)*sc,z))
        d.line([q[:2] for q in pts],fill=cols[c],width=1)
        for q in pts:
            r=4 if q[2]%2==0 else 2; d.ellipse([q[0]-r,q[1]-r,q[0]+r,q[1]+r],outline=cols[c])
            if q[2] in (4,8,12,16): d.text((q[0]+5,q[1]-5),f'{c}{int(q[2])}',fill=cols[c])
    im.save(f'of/{view}_z.png')
