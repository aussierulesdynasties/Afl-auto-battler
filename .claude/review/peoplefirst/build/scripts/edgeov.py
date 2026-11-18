import cv2,numpy as np,json,math,sys
from gpaint_cam import R
D=json.load(open('geo_build.json'));p=json.load(open('cam.json'))['p'];ph=cv2.imread(sys.argv[1] if len(sys.argv)>1 else 'photo_clean.png')
def la(A,a):
    f=(a%360)*4;i=int(f)%1440;t=f-int(f);return A[i]*(1-t)+A[(i+1)%1440]*t
cf=lambda c,a:c[0]+c[1]*math.cos(math.radians(a))+c[2]*math.sin(math.radians(a))
SH=D['roofshift'];Rm=R(*p[3:6])
def pj(X):
    d=(np.array(X)-np.array(p[:3]))@Rm.T;return (int(1000+p[6]*d[0]/d[2]),int(666.5-p[6]*d[1]/d[2]))
for a in np.arange(D['a0'],D['a1'],0.25):
    t=math.radians(a)
    for r,z,c in ((la(D['rout'],a),cf(D['hout'],a),(0,0,255)),(la(D['rin'],a),cf(D['hin'],a),(255,0,0))):
        cv2.circle(ph,pj((r*math.cos(t)+SH[0],r*math.sin(t)+SH[1],z)),1,c,-1)
cv2.imwrite('edgeov.png',ph)
