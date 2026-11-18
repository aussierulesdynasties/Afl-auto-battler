import cv2,numpy as np,sys
P=cv2.imread('photo_clean.png');R=cv2.imread(sys.argv[1] if len(sys.argv)>1 else 'render_r5.png',cv2.IMREAD_UNCHANGED);al=R[...,3];R=R[...,:3]
def gm(x):g=cv2.cvtColor(x,cv2.COLOR_BGR2GRAY).astype(np.float32);return cv2.magnitude(cv2.Sobel(g,cv2.CV_32F,1,0),cv2.Sobel(g,cv2.CV_32F,0,1))
gp,gr=gm(P),gm(R);W=96;out=P.copy()//2
res=[]
for y in range(0,1333-W,48):
    for x in range(0,2000-W,48):
        if (al[y:y+W,x:x+W]>0).mean()<0.9:continue
        a=gp[y:y+W,x:x+W];b=gr[y:y+W,x:x+W]
        if a.std()<8 or b.std()<8:continue
        win=cv2.createHanningWindow((W,W),cv2.CV_32F)
        (dx,dy),resp=cv2.phaseCorrelate(b,a,win)
        if resp<0.12 or abs(dx)>20 or abs(dy)>20:continue
        res.append((x+W//2,y+W//2,dx,dy,resp))
        c=(x+W//2,y+W//2);cv2.arrowedLine(out,c,(int(c[0]+dx*4),int(c[1]+dy*4)),(0,255,255),2,tipLength=0.3)
        cv2.putText(out,'%.0f,%.0f'%(dx,dy),(c[0]-15,c[1]-6),0,0.35,(255,255,255),1)
cv2.imwrite('dmap.jpg',out);r=np.array(res);print(len(r),'median dx,dy',np.median(r[:,2]).round(2),np.median(r[:,3]).round(2),'mean |d|',np.hypot(r[:,2],r[:,3]).mean().round(2))
