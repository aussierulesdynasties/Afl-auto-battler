# z20 Esri tiles over the heritage stands only, resampled into a world grid 0.1 m/px, 100 m square centred at (deg 140, r 112)
import math,io,json,urllib.request,numpy as np,cv2
from PIL import Image
J=json.load(open('sat/sat.json'));M=np.array(J['M']);t=np.array(J['t']);Mi=np.linalg.inv(M)
PC=np.array([0.94,-11.82]);c=PC+112*np.array([math.cos(math.radians(142)),math.sin(math.radians(142))]);HS=70.0;z=20;n=2**z
def ll(X,Y):return Mi[0,0]*(X-t[0])+Mi[0,1]*(Y-t[1]),Mi[1,0]*(X-t[0])+Mi[1,1]*(Y-t[1])
def tl(lo,la):return (lo+180)/360*n,(1-np.arcsinh(np.tan(np.radians(la)))/math.pi)/2*n
xs=[];ys=[]
for X in (c[0]-HS,c[0]+HS):
    for Y in (c[1]-HS,c[1]+HS):a,b=tl(*ll(X,Y));xs.append(a);ys.append(b)
x0,x1,y0,y1=int(min(xs)),int(max(xs)),int(min(ys)),int(max(ys))
im=Image.new('RGB',(256*(x1-x0+1),256*(y1-y0+1)))
for i in range(x0,x1+1):
    for j in range(y0,y1+1):
        u=f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{j}/{i}'
        im.paste(Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'stadium-ref/1.0'})).read())).convert('RGB'),(256*(i-x0),256*(j-y0)))
im=np.asarray(im)[:,:,::-1].copy();Np=1400
jj,ii=np.meshgrid(np.arange(Np),np.arange(Np));X=c[0]-HS+(jj+0.5)*0.1;Y=c[1]+HS-(ii+0.5)*0.1
a,b=tl(*ll(X,Y));out=cv2.remap(im,((a-x0)*256).astype(np.float32),((b-y0)*256).astype(np.float32),cv2.INTER_CUBIC)
cv2.imwrite('sat/her20.png',out);json.dump({'c':c.tolist(),'HS':HS,'mpp':0.1},open('sat/her20.json','w'));print(out.shape,c)
