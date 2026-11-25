import cv2,numpy as np,sys
from arena_fit import robust_ellipse, M, C0
def edge_points(path,rmin=60,rmax=100,nray=720,run=4,k=3.0):
    im=cv2.imread(path).astype(np.float32); im=cv2.GaussianBlur(im,(0,0),1.0)
    s=im.sum(2)+1; f=np.dstack([im[...,1]/s, im[...,2]/s, np.log(s)])   # chromaticity g,r + log brightness
    cx,cy=int(C0[0]),int(C0[1])
    core=f[cy-150:cy+150,cx-150:cx+150].reshape(-1,3)
    mu=core.mean(0); cov=np.cov(core.T)+np.diag([1e-5,1e-5,0.02]); ic=np.linalg.inv(cov)
    d=f-mu; D=np.sqrt(np.einsum('...i,ij,...j->...',d,ic,d))
    pts=[]
    for a in np.linspace(0,2*np.pi,nray,endpoint=False):
        rr=np.arange(rmin/M,rmax/M,0.5); x=C0[0]+rr*np.cos(a); y=C0[1]+rr*np.sin(a)
        v=cv2.remap(D.astype(np.float32),x.astype(np.float32)[None],y.astype(np.float32)[None],cv2.INTER_LINEAR)[0]
        bad=v>k; run_=np.convolve(bad,np.ones(run*2),'valid')>=run*2
        if run_.any():
            i=np.argmax(run_); pts.append((x[i],y[i],a))
    return np.array(pts)
if __name__=='__main__':
    k=float(sys.argv[1])
    for f in sys.argv[2:]:
        P=edge_points(f,k=k); e,keep=robust_ellipse(P)
        im=cv2.imread(f)
        cv2.ellipse(im,((e['cx'],e['cy']),(e['A'],e['B']),e['ang']),(0,0,255),1)
        for (x,y,a),kk in zip(P,keep): cv2.circle(im,(int(x),int(y)),2,(0,255,0) if kk else (255,0,255),-1)
        cv2.imwrite(f.split('.')[0]+'_e3.jpg',im[700:1400,650:1450])
        print(f[3:13],'centre m (%+.2f,%+.2f)'%((e['cx']-C0[0])*M,(e['cy']-C0[1])*M),'axes m %.2f x %.2f'%(max(e['A'],e['B'])*M,min(e['A'],e['B'])*M),'ang %.2f'%e['ang'],'rms m %.2f'%(e['rms']*M),e['kept'],'/',e['n'])
