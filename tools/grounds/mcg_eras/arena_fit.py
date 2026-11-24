# Arena edge by rays: along each ray from the field centre, the last point where the turf's green
# chromaticity holds before the stands; then a robust ellipse fit. Returns metres in this camera.
import cv2,numpy as np,sys
M=0.3019; C0=(1035.25,1037.61)
def chroma(im):
    f=cv2.GaussianBlur(im.astype(np.float32),(0,0),1.2); b,g,r=f[...,0],f[...,1],f[...,2]
    s=b+g+r+1; return g/s, s
def edge_points(path, rmin=55, rmax=105, nray=720):
    im=cv2.imread(path); gc,s=chroma(im)
    # turf green level from the middle of the field
    yy,xx=np.mgrid[-60:61,-60:61]
    core=gc[int(C0[1])-60:int(C0[1])+61,int(C0[0])-60:int(C0[0])+61]
    g0=np.median(core); thr=g0-0.6*(g0-1/3)
    pts=[]
    for a in np.linspace(0,2*np.pi,nray,endpoint=False):
        rr=np.arange(rmin/M,rmax/M,0.5); x=C0[0]+rr*np.cos(a); y=C0[1]+rr*np.sin(a)
        v=cv2.remap(gc,x.astype(np.float32)[None],y.astype(np.float32)[None],cv2.INTER_LINEAR)[0]
        ok=v>thr
        # first sustained drop (10 samples = 5 px) below the threshold going outward
        bad=np.convolve(~ok,np.ones(10),'same')>=9
        i=np.argmax(bad) if bad.any() else None
        if i: pts.append((x[i],y[i],a))
    return np.array(pts)
def robust_ellipse(P,it=10):
    p=P[:,:2].copy(); keep=np.ones(len(p),bool)
    for _ in range(it):
        (cx,cy),(A,B),ang=cv2.fitEllipse(p[keep].astype(np.float32))
        t=np.radians(ang); ca,sa=np.cos(t),np.sin(t); x=p[:,0]-cx; y=p[:,1]-cy
        u=(x*ca+y*sa)/(A/2); v=(-x*sa+y*ca)/(B/2); res=(np.hypot(u,v)-1)*(A+B)/4
        mad=np.median(np.abs(res[keep])); keep=np.abs(res)<max(1.5,3*1.4826*mad)
    return dict(cx=cx,cy=cy,A=A,B=B,ang=ang,rms=float(np.sqrt(np.mean(res[keep]**2))),kept=int(keep.sum()),n=len(p)),keep
if __name__=='__main__':
    for f in sys.argv[1:]:
        P=edge_points(f); e,keep=robust_ellipse(P)
        im=cv2.imread(f)
        cv2.ellipse(im,((e['cx'],e['cy']),(e['A'],e['B']),e['ang']),(0,0,255),1)
        for (x,y,a),k in zip(P,keep): cv2.circle(im,(int(x),int(y)),2,(0,255,0) if k else (255,0,255),-1)
        cv2.imwrite(f.split('.')[0]+'_e2.jpg',im[700:1400,650:1450])
        print(f[3:13],'centre m (%+.2f,%+.2f)'%((e['cx']-C0[0])*M,(e['cy']-C0[1])*M),'axes m %.2f x %.2f'%(max(e['A'],e['B'])*M,min(e['A'],e['B'])*M),'ang %.2f'%e['ang'],'rms m %.2f'%(e['rms']*M),e['kept'],'/',e['n'])
