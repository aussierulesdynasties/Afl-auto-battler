"""Solve the camera of the September 2026 drone photo of Mars Stadium (Wikimedia Commons "Eureka Stadium September
2026", 1920 x 1080, taken from the north-north-east) from the centre square's corners and centre (50 m, on the
field's long axis) and the turf's edge against the fitted fence curve on the far half of the ground:

  python3 tools/grounds/mars/qa/photo_cam.py <photo.jpg> <out_prefix>     -> <out_prefix>.json (camera), .png (overlay)

Unknowns: focal length, rotation, position, one radial distortion term, and a small shift and turn of the painted square
(held near the fit's centre and axis). Used to check the new stands' front wall against the fence curve and the
south-east roof's front height; only numbers are kept, no imagery."""
import sys, json, math, numpy as np, cv2
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from newstands import pol
def ring(b0,b1,off,z,step=0.25):
    bb=np.arange(b0,b1+1e-9,step); p=pol(bb,np.full(len(bb),off)); return np.c_[p,np.full(len(bb),z)]
from PIL import Image, ImageDraw
from scipy.optimize import least_squares
SRC=sys.argv[1]; OUT=sys.argv[2]
im=np.asarray(Image.open(SRC).convert('RGB')).astype(float)
r,g,b=im[...,0],im[...,1],im[...,2]
G=(g>r*1.05)&(g>b*1.25)&(g>60)
G=cv2.morphologyEx(G.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))>0
c0=np.array([995.,648.]); obs=[]; A0,A1=15.0,165.0   # the far half: there the turf edge is the fence's foot, not a roof front hiding it
for a in np.arange(0,360,1.0):
    d=np.array([math.cos(math.radians(a)),-math.sin(math.radians(a))]); last=None; miss=0
    for s in np.arange(5,900,0.5):
        p=c0+s*d; u,v=int(p[0]),int(p[1])
        if not(0<=u<1920 and 0<=v<1080): break
        if G[v,u]: last=s; miss=0
        else:
            miss+=0.5
            if miss>6: break
    if last is not None and A0<a<A1: obs.append([a,last])
obs=np.array(obs)
curves=[ring(0,360,0,0.0), ring(324,384,0.15,7.2), ring(384,458,2.2,6.8)]
ax0=math.radians(31.9); cen0=np.array([-5.4,-5.43])
sq2=np.array([[868.3,601.2],[1149.2,606.7],[805.3,698.7],[1153,709.7],[995,648]])
def sq3(q):
    ax=ax0+q[0]; cen=cen0+q[1:3]; L=np.array([math.sin(ax),math.cos(ax)]); W=np.array([math.cos(ax),-math.sin(ax)])
    P=[cen-25*L+25*W,cen-25*L-25*W,cen+25*L+25*W,cen+25*L-25*W,cen]; return np.c_[np.array(P),np.zeros(5)]
def proj(p,X):
    f=p[0]; k1=p[7]; Rm,_=cv2.Rodrigues(p[1:4]); Xc=X@Rm.T+p[4:7]
    x=Xc[:,0]/Xc[:,2]; y=Xc[:,1]/Xc[:,2]; rr=(x*x+y*y); s=1+k1*rr
    return np.stack([960+f*x*s,540+f*y*s],1)
def pred(p):
    out=np.full(len(obs),1e4)
    for C in curves:
        P=proj(p,C)-c0; ang=np.unwrap(np.arctan2(-P[:,1],P[:,0])); rad=np.hypot(*P.T)
        if ang[-1]<ang[0]: ang=ang[::-1]; rad=rad[::-1]
        if np.any(np.diff(ang)<=0):
            o=np.argsort(ang); ang=ang[o]; rad=rad[o]
        A=np.radians(obs[:,0])
        for sh in (-2,-1,0,1,2):
            Aa=A+sh*2*np.pi; m=(Aa>=ang[0])&(Aa<=ang[-1])
            if m.any(): out[m]=np.minimum(out[m],np.interp(Aa[m],ang,rad))
    return out
def res(p,full=True):
    e=(proj(p,sq3(p[8:11]))-sq2).ravel()*3
    if not full: return np.r_[e,p[9]*5,p[10]*5,p[8]*300,p[7]*100]
    d=pred(p)-obs[:,1]; d=np.clip(d,-60,60)
    return np.concatenate([e,d,[p[9]*5,p[10]*5,math.degrees(p[8])*5,p[7]*100]])
best=None
cen=np.array([-5.4,-5.43,0]); L=np.array([math.sin(ax0),math.cos(ax0),0])
for f0 in (1000,1600):
  for dist in (200,350):
    for h in (80,200):
        cam=cen+dist*L+np.array([0,0,h]); fwd=(cen-cam); fwd/=np.linalg.norm(fwd)
        right=np.cross(fwd,[0,0,1]); right/=np.linalg.norm(right); down=np.cross(fwd,right)
        Rm=np.stack([right,down,fwd]); rv,_=cv2.Rodrigues(Rm); t=-Rm@cam
        p0=np.r_[f0,rv.ravel(),t,0,0,0,0]
        s=least_squares(res,p0,args=(False,),loss='soft_l1')
        if best is not None and s.cost>best.cost*50: continue
        s=least_squares(res,s.x,loss='soft_l1',f_scale=3)
        if best is None or s.cost<best.cost: best=s
p=best.x; Rm,_=cv2.Rodrigues(p[1:4]); cam=-Rm.T@p[4:7]
d=pred(p)-obs[:,1]
print('f %.0f k1 %.3f cam %s  square shift %s axis %+.2f deg'%(p[0],p[7],np.round(cam,1),np.round(p[9:11],2),math.degrees(p[8])))
print('square px max %.1f; fence px median %.2f p90 %.2f n %d'%(np.abs(proj(p,sq3(p[8:11]))-sq2).max(),np.median(np.abs(d)),np.percentile(np.abs(d),90),len(d)))
json.dump({'p':[float(v) for v in p]},open(OUT+'.json','w'))
o=Image.open(SRC).convert('RGB'); dr=ImageDraw.Draw(o)
for C,col in zip(curves,[(255,0,255),(0,255,255),(255,128,0)]):
    for q in proj(p,C): dr.point(tuple(q),fill=col)
for a,s in obs:
    q=c0+s*np.array([math.cos(math.radians(a)),-math.sin(math.radians(a))]); dr.point(tuple(q),fill=(255,255,0))
for q in proj(p,sq3(p[8:11])): dr.ellipse([q[0]-3,q[1]-3,q[0]+3,q[1]+3],outline=(255,0,0))
o.save(OUT+'.png')
