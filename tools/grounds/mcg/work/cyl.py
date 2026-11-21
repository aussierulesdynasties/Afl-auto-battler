# Cylindrical sweep of the bowl's inner face: for each (bearing, height) cell pick the radius where the views agree.
# python work/cyl.py out.npz views...   grid: bearing 0..360 step 0.5 deg, z 0..50 step 0.5 m, sweep r 68..150 step 0.5
import sys,cv2,numpy as np;sys.path.insert(0,'work');import earthcam as E,tri as T
out=sys.argv[1];V=sys.argv[2:]
B=np.radians(np.arange(0,360,0.5));Z=np.arange(50,-0.01,-0.5);GB,GZ=np.meshgrid(B,Z)
IM={v:cv2.cvtColor(cv2.imread(f'ge/{v}.png'),cv2.COLOR_BGR2GRAY).astype(np.float32) for v in V}
for v in V: IM[v][:90]=np.nan;IM[v][1040:]=np.nan
CC={v:T.camv(v) for v in V}
def warp(v,r):
    c=CC[v];X=r*np.sin(GB);Y=r*np.cos(GB);D=np.stack([X-c['C'][0],Y-c['C'][1],GZ-c['C'][2]],-1);zc=D@c['fwd']
    # facing test: the cell's inward normal (towards the field) must face the camera
    nx,ny=-np.sin(GB),-np.cos(GB);face=(-(D[...,0]*nx+D[...,1]*ny))>0
    u=c['W']/2+c['f']*(D@c['right'])/zc;w=c['H']/2-c['f']*(D@c['up'])/zc
    o=cv2.remap(IM[v],u.astype(np.float32),w.astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=np.nan)
    o[~face]=np.nan;return o
K=(5,5)
def stats(a):
    m=cv2.boxFilter(a,-1,K);s=np.sqrt(np.maximum(cv2.boxFilter(a*a,-1,K)-m*m,1e-3));return m,s
best=np.full(GB.shape,-2.0,np.float32);br=np.zeros(GB.shape,np.float32)
for r in np.arange(68,150,0.5):
    S=np.stack([warp(v,r) for v in V]);ok=~np.isnan(S);S0=np.nan_to_num(S);med=np.nan_to_num(np.nanmedian(S,0));mm,ms=stats(med);sc=[]
    for i in range(len(V)):
        a=S0[i];am,asd=stats(a);n=(cv2.boxFilter(a*med,-1,K)-am*mm)/(asd*ms);n[~ok[i]]=-1;sc.append(n)
    sc=np.sort(np.stack(sc),0)[-3:].mean(0);u=sc>best;best[u]=sc[u];br[u]=r
np.savez_compressed(out,r=br,score=best)
v=cv2.applyColorMap(np.clip((br-68)/82*255,0,255).astype(np.uint8),cv2.COLORMAP_JET);v[best<0.3]//=3
v=cv2.resize(v,None,fx=2,fy=4,interpolation=cv2.INTER_NEAREST)
for b in range(0,360,30): cv2.line(v,(b*4,0),(b*4,v.shape[0]),(255,255,255),1);cv2.putText(v,str(b),(b*4+2,12),0,0.4,(255,255,255),1)
for z in range(0,51,10): y=int((50-z)/0.5*4);cv2.line(v,(0,y),(v.shape[1],y),(255,255,255),1);cv2.putText(v,str(z),(2,y-2),0,0.4,(255,255,255),1)
cv2.imwrite(out.replace('.npz','.png'),v)
