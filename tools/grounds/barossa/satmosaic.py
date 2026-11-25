"""Google satellite mosaic round the fence centre, north up, for measuring only (tree crowns, row bearings, roof
colours, tracing): python3 satmosaic.py ZOOM HALF_M RES_M OUT.png. Tiles cached in work/tiles."""
import sys, os, math, urllib.request, numpy as np, cv2
from concurrent.futures import ThreadPoolExecutor
LAT0, LON0 = -34.5984014, 138.8858792
Z=int(sys.argv[1]); HALF=float(sys.argv[2]); RES=float(sys.argv[3]); OUT=sys.argv[4]
N=2**Z
p=math.radians(LAT0); MLAT=111132.92-559.82*math.cos(2*p)+1.175*math.cos(4*p); MLON=111412.84*math.cos(p)-93.5*math.cos(3*p)
def txy(lat,lon): return (lon+180)/360*N,(1-math.log(math.tan(math.radians(lat))+1/math.cos(math.radians(lat)))/math.pi)/2*N
tx0,ty0=txy(LAT0+HALF/MLAT,LON0-HALF/MLON); tx1,ty1=txy(LAT0-HALF/MLAT,LON0+HALF/MLON)
X0,Y0,X1,Y1=int(tx0),int(ty0),int(tx1),int(ty1)
TD=os.path.join(os.path.dirname(os.path.abspath(__file__)),'work','tiles'); os.makedirs(TD,exist_ok=True)
def get(a):
    tx,ty=a; f=os.path.join(TD,'g%d_%d_%d.jpg'%(Z,tx,ty))
    if not os.path.exists(f):
        rq=urllib.request.Request('https://mt1.google.com/vt/lyrs=s&x=%d&y=%d&z=%d'%(tx,ty,Z),headers={'User-Agent':'Mozilla/5.0'})
        open(f,'wb').write(urllib.request.urlopen(rq,timeout=30).read())
    return f
jobs=[(tx,ty) for ty in range(Y0,Y1+1) for tx in range(X0,X1+1)]
with ThreadPoolExecutor(8) as ex: fs=list(ex.map(get,jobs))
big=np.zeros(((Y1-Y0+1)*256,(X1-X0+1)*256,3),np.uint8)
for (tx,ty),f in zip(jobs,fs): big[(ty-Y0)*256:(ty-Y0+1)*256,(tx-X0)*256:(tx-X0+1)*256]=cv2.imread(f)
n=int(2*HALF/RES); xs=-HALF+(np.arange(n)+0.5)*RES; ys=HALF-(np.arange(n)+0.5)*RES
X,Y=np.meshgrid(xs,ys); lat=LAT0+Y/MLAT; lon=LON0+X/MLON
mx=((lon+180)/360*N-X0)*256; my=((1-np.log(np.tan(np.radians(lat))+1/np.cos(np.radians(lat)))/np.pi)/2*N-Y0)*256
out=cv2.remap(big,mx.astype(np.float32)-0.5,my.astype(np.float32)-0.5,cv2.INTER_AREA if RES>0.6 else cv2.INTER_CUBIC)
cv2.imwrite(OUT,out); print(out.shape,len(jobs))
