"""Measured oblique check (docs/MCG_STANDARD.md): each Google Earth shot against ours, edge maps phase-correlated over a 3 x 3 grid of
windows (each 1/3 of the picture); a window's offset in pixels -> metres at the view's target distance.

    python3 qa/oblique_measure.py <workdir> <views.json>     # after ge_compare.py sheet
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter
work=sys.argv[1]; views=json.load(open(sys.argv[2]))
FOV=2*math.degrees(math.atan(math.tan(math.radians(17.5))*720/1000))
def edges(p):
    im=Image.open(p).convert('L').resize((960,540))
    a=np.asarray(im.filter(ImageFilter.GaussianBlur(1.2)),float)
    gx=np.zeros_like(a); gy=np.zeros_like(a); gx[:,1:-1]=a[:,2:]-a[:,:-2]; gy[1:-1]=a[2:]-a[:-2]
    return np.hypot(gx,gy)
def pc(A,B):
    A=(A-A.mean())*np.hanning(A.shape[0])[:,None]*np.hanning(A.shape[1])[None]; B=(B-B.mean())*np.hanning(B.shape[0])[:,None]*np.hanning(B.shape[1])[None]
    F=np.fft.fft2(A)*np.conj(np.fft.fft2(B)); c=np.fft.ifft2(F/np.maximum(abs(F),1e-9)).real
    y,x=np.unravel_index(np.argmax(c),c.shape); peak=c[y,x]/c.std()
    if y>A.shape[0]/2: y-=A.shape[0]
    if x>A.shape[1]/2: x-=A.shape[1]
    return x,y,peak
rows=[]
for v in views:
    g=os.path.join(work,'ge',v['name']+'.png'); o=os.path.join(work,'ours','norwood_%s.png'%v['name'])
    if not (os.path.exists(g) and os.path.exists(o)) or 'd' not in v: continue
    A,B=edges(g),edges(o)
    mpp=2*v['d']*math.tan(math.radians(FOV/2))/540
    sh=[]
    for i in range(3):
        for j in range(3):
            a=A[i*180:(i+1)*180,j*320:(j+1)*320]; b=B[i*180:(i+1)*180,j*320:(j+1)*320]
            if a.std()<2 or b.std()<2: continue
            x,y,pk=pc(a,b)
            if pk>8: sh.append(math.hypot(x,y)*mpp)
    x,y,pk=pc(A,B)
    rows.append((v['name'],v['d'],math.hypot(x,y)*mpp,pk,np.median(sh) if sh else float('nan'),max(sh) if sh else float('nan'),len(sh)))
print('%-8s %6s %8s %6s %8s %8s %4s'%('view','d m','whole m','peak','win med','win max','n'))
for r in rows: print('%-8s %6.0f %8.2f %6.1f %8.2f %8.2f %4d'%r)
w=[r[2] for r in rows if r[3]>8]
print('views %d, whole-picture offset (confident ones %d): median %.2f m, max %.2f m'%(len(rows),len(w),np.median(w) if w else float('nan'),max(w) if w else float('nan')))
