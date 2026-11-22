# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import numpy as np, json, math, cv2, sys
import os; ENGIE_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model', 'engie.json')
from cam import camera, project
from scipy.optimize import least_squares
C=json.load(open('cal.json')); DX,DY=C['dx'],C['dy']
D=json.load(open(ENGIE_JSON))
def per(t,q):
    t=np.array(sorted(t),float); return np.interp(np.asarray(q)%360,np.r_[t[:,0]-360,t[:,0],t[:,0]+360],np.r_[t[:,1],t[:,1],t[:,1]])
bs=np.arange(0,360,0.5)
F=per(D['fence'],bs); G=per(D['front_gap'],bs); RF=per(D['rf'],bs); RB=per(D['rb'],bs)
r0=F+G; a0=r0+0.3; a1=a0+15*0.8; c0=a1+1.8; c1=c0+12*0.8; bw=RB-1.5
openm=(bs>=8)&(bs<=72)
GAPS=[(135.4,141.4),(172.2,178.2),(205.8,211.8),(239.3,245.3),(272.3,278.3),(309.3,315.3),(72,77),(363-360,8)]
roofm=~openm
def rooftop(b,front):
    out=[]
    for bb in b:
        if 315.3<=bb or bb<=3: xs,zs=[315.3,330,345,363],[21.5,21.3,19.0,18.0]; q=bb if bb>=315.3 else bb+360; zf=np.interp(q,xs,zs); out.append(zf if front else 18.0)
        elif 77<=bb<=135.4: zf=np.interp(bb,[77,106,120,135.4],[18.2,18.4,21.3,21.3]); out.append(zf if front else 18.0)
        else:
            st=[(141.4,172.2),(178.2,205.8),(211.8,239.3),(245.3,272.3),(278.3,309.3)]
            arch=0
            for a,c in st:
                if a<=bb<=c: arch=3.2*math.sin(math.pi*(bb-a)/(c-a))
            out.append((21.5 if front else 18.3)+arch)
    return np.array(out)
LINES={'field edge z0':(F,np.zeros_like(bs),(0,255,255),None),
       'stand front top':(r0,np.full_like(bs,1.4),(255,255,0),None),
       'lower tier top':(a1,np.where(openm,np.nan,6.8),(0,165,255),None),
       'upper tier front':(c0,np.where(openm,np.nan,9.9),(255,0,255),None),
       'roof front':(RF,np.where(openm,np.nan,rooftop(bs,True)),(0,255,0),None),
       'roof back':(RB,np.where(openm,np.nan,rooftop(bs,False)),(0,0,255),None),
       'wall base':(bw,np.zeros_like(bs),(255,255,255),None)}
def draw(h,Delta,out):
    im=cv2.imread('ge/ob_%03d.png'%h)
    cam=camera((DX,DY,Delta),h,50,1200,15)
    for nm,(r,z,col,_) in LINES.items():
        P=np.c_[r*np.sin(np.radians(bs)),r*np.cos(np.radians(bs)),z]
        Q=project(cam,P)
        # draw only the side facing the camera for wall base (near side), all else everywhere
        for i in range(len(bs)-1):
            if np.isnan(Q[i]).any() or np.isnan(Q[i+1]).any(): continue
            cv2.line(im,tuple(int(v) for v in Q[i]),tuple(int(v) for v in Q[i+1]),col,1,cv2.LINE_AA)
    cv2.imwrite(out,im)
if __name__=='__main__':
    h=int(sys.argv[1]); Delta=float(sys.argv[2]); draw(h,Delta,sys.argv[3])
