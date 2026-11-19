# python satwb.py RELEASE OUT.png  -> same frame as sat/esri_025.png (CX50 CY30 HALF200 0.25 m/px)
import sys,os,math,urllib.request,numpy as np,cv2
sys.path.insert(0,'.');import geo
REL,OUT=sys.argv[1],sys.argv[2]
Z=19;RES=0.25;N=2**Z;CX,CY,HALF=50,30,200
def txy(lat,lon): return (lon+180)/360*N,(1-math.log(math.tan(math.radians(lat))+1/math.cos(math.radians(lat)))/math.pi)/2*N
la0,lo0=geo.xy2ll(CX-HALF,CY+HALF);la1,lo1=geo.xy2ll(CX+HALF,CY-HALF)
X0,Y0=map(int,txy(la0,lo0));X1,Y1=map(int,txy(la1,lo1))
os.makedirs(f'wb/{REL}',exist_ok=True)
big=np.zeros(((Y1-Y0+1)*256,(X1-X0+1)*256,3),np.uint8)
for ty in range(Y0,Y1+1):
  for tx in range(X0,X1+1):
    f=f'wb/{REL}/{tx}_{ty}.jpg'
    if not os.path.exists(f):
      rq=urllib.request.Request(f'https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/{REL}/{Z}/{ty}/{tx}',headers={'User-Agent':'Mozilla/5.0'})
      open(f,'wb').write(urllib.request.urlopen(rq,timeout=30).read())
    big[(ty-Y0)*256:(ty-Y0+1)*256,(tx-X0)*256:(tx-X0+1)*256]=cv2.imread(f)
n=int(2*HALF/RES);xs=CX-HALF+(np.arange(n)+0.5)*RES;ys=CY+HALF-(np.arange(n)+0.5)*RES
X,Y=np.meshgrid(xs,ys);lat=geo.LAT0+Y/geo.MLAT;lon=geo.LON0+X/geo.MLON
mx=((lon+180)/360*N-X0)*256;my=((1-np.log(np.tan(np.radians(lat))+1/np.cos(np.radians(lat)))/np.pi)/2*N-Y0)*256
cv2.imwrite(OUT,cv2.remap(big,mx.astype(np.float32)-0.5,my.astype(np.float32)-0.5,cv2.INTER_CUBIC));print('ok')
