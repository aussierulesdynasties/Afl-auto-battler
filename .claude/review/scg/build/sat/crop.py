# crop sat_world (and optional model top) around a polar point: crop.py deg r size_m out [top.png]
import cv2,sys,math,numpy as np
d,r,sz=map(float,sys.argv[1:4]);out=sys.argv[4];N=1700;H=170.0
x=r*math.cos(math.radians(d));y=r*math.sin(math.radians(d));px=(x+H)/(2*H)*N;py=(H-y)/(2*H)*N;h=sz/2/(2*H)*N
def cr(im):
    c=im[int(py-h):int(py+h),int(px-h):int(px+h)];c=cv2.resize(c,(800,800),interpolation=cv2.INTER_CUBIC)
    for k in range(-60,61,5):   # 5 m grid lines relative to the crop centre
        q=int(400+k/sz*800);cv2.line(c,(q,0),(q,800),(0,255,255) if k%25==0 else (0,120,120),1);cv2.line(c,(0,q),(800,q),(0,255,255) if k%25==0 else (0,120,120),1)
    return c
s=cr(cv2.imread('sat/sat_world.png'))
if len(sys.argv)>5:
    t=cv2.imread(sys.argv[5],cv2.IMREAD_UNCHANGED);a=t[...,3:4]/255.;bl=(cv2.imread('sat/sat_world.png')*(1-0.55*a)+t[...,:3]*0.55*a).astype(np.uint8);s=np.hstack([s,cr(bl)])
cv2.imwrite(out,s)
