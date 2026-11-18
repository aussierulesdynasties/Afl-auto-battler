# Measure, per azimuth, the photo's roof outer edge and the z that puts (rout,z) on it.
import cv2,numpy as np,json,math
from gpaint_cam import R
D=json.load(open('geo_build.json'));p=json.load(open('cam.json'))['p'];ph=cv2.imread('photo_clean.png').astype(int)
def la(A,a):
    f=(a%360)*4;i=int(f)%1440;t=f-int(f);return A[i]*(1-t)+A[(i+1)%1440]*t
cf=lambda c,a:c[0]+c[1]*math.cos(math.radians(a))+c[2]*math.sin(math.radians(a))
SH=D['roofshift'];Rm=R(*p[3:6])
def pj(X):
    d=(np.array(X)-np.array(p[:3]))@Rm.T;return np.array([1000+p[6]*d[0]/d[2],666.5-p[6]*d[1]/d[2]])
white=(ph.min(2)>222)&((ph.max(2)-ph.min(2))<28)
rows=[]
for a in np.arange(D['a0'],D['a1'],0.25):
    t=math.radians(a);ro=la(D['rout'],a);z0=cf(D['hout'],a);ri=la(D['rin'],a)
    P0=pj((ro*math.cos(t)+SH[0],ro*math.sin(t)+SH[1],z0));Pi=pj((ri*math.cos(t)+SH[0],ri*math.sin(t)+SH[1],cf(D['hin'],a)))
    P1=pj((ro*math.cos(t)+SH[0],ro*math.sin(t)+SH[1],z0+1));pxm=P0[1]-P1[1]
    x=int(round(P0[0]));y=int(round(P0[1]))
    if not(5<x<1995 and 50<y<1290):continue
    near=P0[1]>Pi[1];col=white[:,x];best=None
    for dy in range(-45,46):
        yy=y+dy
        if near and col[yy-4:yy].all() and not col[yy+1:yy+4].any():
            if best is None or abs(dy)<abs(best):best=dy
        if (not near) and col[yy+1:yy+5].all() and not col[yy-3:yy].any():
            if best is None or abs(dy)<abs(best):best=dy
    rows.append((float(a),bool(near),best,float(pxm)))
json.dump(rows,open('edgefit.json','w',newline=''))
for r in rows[::16]:print(round(r[0],1),r[1],r[2],round(r[3],1))
print(len(rows),sum(r[2] is not None for r in rows))
