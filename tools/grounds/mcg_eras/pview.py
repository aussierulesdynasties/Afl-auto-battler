# Polar strip of one capture with a labelled grid (bearing across, metres from the field centre up).
import cv2,numpy as np,json,sys
M=0.3019
C=json.load(open('centres.json'))
def view(f,b0,b1,r0,r1,out,db=0.1,dr=0.2,scale=2):
    cx,cy=C[f]; im=cv2.imread(f)
    bb=np.arange(b0,b1,db); rr=np.arange(r1,r0,-dr)
    B,R=np.meshgrid(np.radians(bb),rr)
    X=(cx+R*np.sin(B)/M).astype(np.float32); Y=(cy-R*np.cos(B)/M).astype(np.float32)
    p=cv2.remap(im,X,Y,cv2.INTER_CUBIC)
    p=cv2.resize(p,(p.shape[1]*scale//2,p.shape[0]*scale//2),interpolation=cv2.INTER_CUBIC) if scale!=2 else p
    H,W=p.shape[:2]; sx=W/len(bb); sy=H/len(rr)
    for b in np.arange(np.ceil(b0),b1,1.0):
        x=int((b-b0)/db*sx); c=(0,0,255) if b%5==0 else (0,200,255)
        p[:,x]=c if b%5==0 else p[:,x]
        if b%5!=0: p[:8,x]=c; p[-8:,x]=c
        if b%5==0: cv2.putText(p,'%d'%(b%360),(x+2,12),cv2.FONT_HERSHEY_PLAIN,0.9,(255,255,255),1)
    for r in np.arange(np.floor(r0)+1,r1,1.0):
        y=int((r1-r)/dr*sy)
        if r%10==0: p[y]=(0,0,255); cv2.putText(p,'%d'%r,(2,y-2),cv2.FONT_HERSHEY_PLAIN,0.9,(255,255,255),1)
        elif r%5==0: p[y,::4]=(0,200,255)
        else: p[y,:8]=(0,200,255); p[y,-8:]=(0,200,255)
    cv2.imwrite(out,p)
if __name__=='__main__':
    a=sys.argv; view(a[1],float(a[2]),float(a[3]),float(a[4]),float(a[5]),a[6])
