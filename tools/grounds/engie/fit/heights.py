# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import numpy as np, json, math
f=3858.6; B=150.0
C=json.load(open('cal.json')); DX,DY=C['dx'],C['dy']; FIT=json.load(open('fit.json'))
dWE=np.load('dWE.npy'); dSN=np.load('dSN.npy')
def grid(d,ce,cn,h_est=0):
    return d
# ground disparity from the field
def pix(e,n,ce,cn,Dg,h):
    s=(Dg-h)/f; return 640+(e-DX-ce)/s, 360-(n-DY-cn)/s
dg_we=np.nanmedian(dWE[300:420,560:720]); dg_sn=np.nanmedian(dSN[300:420,560:720])
Dg=f*B/dg_we; print('field disparity WE %.2f SN %.2f -> camera %.1f m above field'%(dg_we,dg_sn,Dg))
def H(e,n):
    out=[]
    for d,ce,cn,dg in ((dWE,-75,0,dg_we),(dSN,0,75,dg_sn)):
        v=[]
        for it in range(3):
            h=np.nanmedian(v) if v else 15
            x,y=pix(e,n,ce,cn,Dg,h); xi,yi=int(round(x)),int(round(y))
            if not(3<=xi<1277 and 60<=yi<717): break
            w=d[yi-2:yi+3,xi-2:xi+3]; 
            if np.isnan(w).all(): break
            v=[f*B*(1/dg-1/np.nanmedian(w))]
        out.append(v[0] if v else np.nan)
    return out
p=np.array(FIT['p']); K=FIT['K']
T=np.radians(np.arange(0,360,2.0))
def ringpt(t,dd):
    r=p[2]+sum(p[2+2*k-1]*np.cos(k*t)+p[2+2*k]*np.sin(k*t) for k in range(1,K+1))
    x=p[0]+r*np.sin(t); y=p[1]+r*np.cos(t)
    # normal by finite difference
    t2=t+1e-3; r2=p[2]+sum(p[2+2*k-1]*np.cos(k*t2)+p[2+2*k]*np.sin(k*t2) for k in range(1,K+1))
    x2=p[0]+r2*np.sin(t2); y2=p[1]+r2*np.cos(t2); L=math.hypot(x2-x,y2-y); nx,ny=(y2-y)/L,-(x2-x)/L
    return x-dd*nx, y-dd*ny   # outward = -normal (see fit offsets)
dF,dB=-p[-2],-p[-1]
rows=[]
for t in T:
    b=math.degrees(t)
    hf=H(*ringpt(t,dF+2.0)); hb=H(*ringpt(t,dB-2.0)); hm=H(*ringpt(t,(dF+dB)/2))
    rows.append([b,*hf,*hm,*hb])
R=np.array(rows); np.save('roofh.npy',R)
ST={'N 2012':(315.3,363),'E 2012':(77,135.4),'SE':(141.4,172.2),'S':(178.2,205.8),'SW':(211.8,239.3),'W':(245.3,272.3),'NW':(278.3,309.3),'NE open':(8,72)}
for nm,(a,b) in ST.items():
    m=((R[:,0]-a)%360)<=(b-a)
    print('%-8s front %5.1f/%5.1f  mid %5.1f/%5.1f  back %5.1f/%5.1f  (WE/SN medians, m above field)'%(nm,*[np.nanmedian(R[m,k]) for k in range(1,7)]))
print('NE open stand profile (offset from field edge -> height m, WE/SN):')
for dd in range(0,34,2):
    v=[H(*ringpt(math.radians(b),dd)) for b in range(22,60,3)]
    v=np.array(v); print('  %2d m: %5.1f %5.1f'%(dd,np.nanmedian(v[:,0]),np.nanmedian(v[:,1])))
