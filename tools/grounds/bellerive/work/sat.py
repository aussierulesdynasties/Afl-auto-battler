# Esri World Imagery z19 -> local 0.25 m/px north-up mosaic, extent +-HALF m around origin
import sys,os,math,urllib.request,numpy as np,cv2
sys.path.insert(0,os.path.dirname(__file__));import geo
Z=19;HALF=200;RES=0.25;N=2**Z
def tile_xy(lat,lon):
  x=(lon+180)/360*N;y=(1-math.log(math.tan(math.radians(lat))+1/math.cos(math.radians(lat)))/math.pi)/2*N;return x,y
la0,lo0=geo.xy2ll(-HALF,HALF);la1,lo1=geo.xy2ll(HALF,-HALF)
tx0,ty0=tile_xy(la0,lo0);tx1,ty1=tile_xy(la1,lo1)
X0,Y0,X1,Y1=int(tx0),int(ty0),int(tx1),int(ty1)
os.makedirs('sat/t',exist_ok=True)
big=np.zeros(((Y1-Y0+1)*256,(X1-X0+1)*256,3),np.uint8)
for ty in range(Y0,Y1+1):
  for tx in range(X0,X1+1):
    f=f'sat/t/{tx}_{ty}.jpg'
    if not os.path.exists(f):
      rq=urllib.request.Request(f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{Z}/{ty}/{tx}',headers={'User-Agent':'Mozilla/5.0'})
      open(f,'wb').write(urllib.request.urlopen(rq,timeout=30).read())
    big[(ty-Y0)*256:(ty-Y0+1)*256,(tx-X0)*256:(tx-X0+1)*256]=cv2.imread(f)
n=int(2*HALF/RES);xs=-HALF+(np.arange(n)+0.5)*RES;ys=HALF-(np.arange(n)+0.5)*RES
X,Y=np.meshgrid(xs,ys);lat=geo.LAT0+Y/geo.MLAT;lon=geo.LON0+X/geo.MLON
mx=((lon+180)/360*N-X0)*256;my=((1-np.log(np.tan(np.radians(lat))+1/np.cos(np.radians(lat)))/np.pi)/2*N-Y0)*256
out=cv2.remap(big,mx.astype(np.float32)-0.5,my.astype(np.float32)-0.5,cv2.INTER_CUBIC)
cv2.imwrite('sat/esri_025.png',out);print(out.shape,(X1-X0+1)*(Y1-Y0+1),'tiles')
