# ground layout classes from the satellite (layout only; colours come later from the main photo as numbers)
import cv2,numpy as np
sat=cv2.imread('g_sat.png');N=sat.shape[0];lb=np.load('g_km.npy')
hsv=cv2.cvtColor(sat,cv2.COLOR_BGR2HSV).astype(float);V=hsv[...,2];H=hsv[...,0];Sa=hsv[...,1]
g=cv2.cvtColor(sat,cv2.COLOR_BGR2GRAY).astype(np.float32)
std=np.sqrt(np.maximum(cv2.blur(g*g,(9,9))-cv2.blur(g,(9,9))**2,0))
green=(H>28)&(H<90)&(Sa>45)
# 0 asphalt-mid 1 asphalt-light 2 asphalt-dark 3 concrete/pale 4 grass 5 trees 6 water 7 roofs(footprints)
C=np.zeros((N,N),np.uint8)
C[np.isin(lb,[5,2])]=1;C[np.isin(lb,[8])]=2;C[np.isin(lb,[7,10])]=3;C[lb==1]=7
C[green]=4
tr=np.isin(lb,[6,11])&(H>25)&(H<95)&(Sa>30)&(std>7);tr=cv2.morphologyEx(tr.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))>0;C[tr]=5
dark=(lb==3).astype(np.uint8);dark=cv2.morphologyEx(dark,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
n,cc=cv2.connectedComponents(dark);w=cc[100,1900];C[(cc==w)&(w>0)]=6
C[(lb==3)&(C!=6)]=2;C[(lb==6)&~green&(C!=5)]=2
import json
D=json.load(open('geo_build.json'));RO=np.array(D['rout'])
xs=(np.arange(N)+0.5)/(N/400)-200;X,Y=np.meshgrid(xs,-xs);rr=np.hypot(X,Y);aa=(np.degrees(np.arctan2(Y,X))%360*4).astype(int)%1440
C[np.isin(C,[1,2])&(rr<RO[aa]+30)]=0   # roof shadow on the concourse asphalt -> the asphalt itself
# clean: per-class one-hot median -> majority
oh=np.stack([(C==k).astype(np.float32) for k in range(8)]);oh=np.stack([cv2.GaussianBlur(o,(0,0),2.0) for o in oh]);C=oh.argmax(0).astype(np.uint8)
np.save('g_cls.npy',C)
# painted lines: thin bright marks on asphalt/grass (not cars: opening 3x3 removes thin lines only)
th=cv2.morphologyEx(g,cv2.MORPH_TOPHAT,np.ones((7,7),np.uint8));m=(th>18).astype(np.uint8)
thin=m&(1-cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)))
n,cc,st,_=cv2.connectedComponentsWithStats(thin)
keep=np.zeros(n,bool)
for i in range(1,n):
    w_,h_,a_=st[i,2],st[i,3],st[i,4]
    if max(w_,h_)>=6 and a_<=2.2*max(w_,h_):keep[i]=True
L=keep[cc]&np.isin(C,[0,1,2,4]);np.save('g_lines.npy',L)
pal=np.array([[110,110,118],[150,150,156],[70,72,80],[200,205,210],[60,150,70],[30,80,40],[90,50,20],[255,255,255]],np.uint8)
vis=pal[C];vis[L]=(0,255,255)
cv2.imwrite('g_cls.jpg',np.hstack([cv2.resize(sat,(1024,1024)),cv2.resize(vis,(1024,1024),interpolation=cv2.INTER_AREA)]))
print(np.bincount(C.ravel(),minlength=8),L.sum())
