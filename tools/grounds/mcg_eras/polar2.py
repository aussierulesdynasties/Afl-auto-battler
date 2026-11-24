import cv2,numpy as np,sys,json
M=0.3019
def strip(path,cx,cy,b0,b1,r0=60,r1=170,db=0.1,dr=0.25):
    im=cv2.imread(path)
    b=np.radians(np.arange(b0,b1,db)); r=np.arange(r0,r1,dr)
    B,R=np.meshgrid(b,r)
    X=(cx+R*np.sin(B)/M).astype(np.float32); Y=(cy-R*np.cos(B)/M).astype(np.float32)
    p=cv2.remap(im,X,Y,cv2.INTER_LINEAR)[::-1].copy()
    H=p.shape[0]
    for k,bb in enumerate(np.arange(b0,b1,db)):
        if abs(bb-round(bb/10)*10)<db/2: p[:,k]=(0,255,255) if round(bb)%30 else (0,0,255)
    for rr in range(r0+10,r1,10): p[H-1-int((rr-r0)/dr)]=(0,0,255) if rr%50==0 else (0,180,255)
    return p
if __name__=='__main__':
    C=json.load(open('centres.json'))
    b0,b1=float(sys.argv[1]),float(sys.argv[2]); out=sys.argv[3]
    rows=[]
    for f in sys.argv[4:]:
        cx,cy=C[f]; s=strip(f,cx,cy,b0,b1)
        cv2.putText(s,f[3:13],(10,30),cv2.FONT_HERSHEY_SIMPLEX,0.9,(255,255,255),2); rows.append(s)
    cv2.imwrite(out,np.vstack(rows))
