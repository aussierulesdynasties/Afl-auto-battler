import cv2,numpy as np,json
S=json.load(open('sat.json'));m=S['mpp'];im=cv2.imread('sat.png')
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
g=((hsv[...,0]>30)&(hsv[...,0]<75)&(hsv[...,1]>60)).astype(np.uint8)*255
g=cv2.morphologyEx(g,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(g)
cx,cy=int(S['px']),int(S['py']);box=lab[cy-100:cy+100,cx-100:cx+100];vals,cnt=np.unique(box[box>0],return_counts=True);k=vals[np.argmax(cnt)]
g=(lab==k).astype(np.uint8)*255;g=cv2.morphologyEx(g,cv2.MORPH_CLOSE,np.ones((41,41),np.uint8))
cnts,_=cv2.findContours(g,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);g=np.zeros_like(g);cv2.drawContours(g,cnts,-1,255,-1)
D=json.load(open('geo_build.json'));RG=np.array(D['RG'])
N=1440;rs=np.arange(20,120,0.05);out=np.zeros(N)
for i in range(N):
    a=2*np.pi*i/N;u=(S['px']+rs*np.cos(a)/m).astype(int);v=(S['py']-rs*np.sin(a)/m).astype(int)
    on=g[v,u]>0;j=np.where(~on)[0];out[i]=rs[j[0]] if len(j) else rs[-1]
F=np.fft.rfft(out);F[13:]=0;sm=np.fft.irfft(F,N)
print('raw-sm max',np.abs(out-sm).max().round(2),'sm-RG mean',(sm-RG).mean().round(2),'min',(sm-RG).min().round(1),'max',(sm-RG).max().round(1))
for a in range(0,360,30):print(a,round(out[a*4],1),round(sm[a*4],1),round(RG[a*4],1))
np.save('rg_sat.npy',sm)
ov=im.copy()
for arr,col in ((sm,(255,0,255)),(RG,(255,128,0))):
    pts=np.array([[S['px']+arr[i]*np.cos(2*np.pi*i/N)/m,S['py']-arr[i]*np.sin(2*np.pi*i/N)/m] for i in range(N)],np.int32);cv2.polylines(ov,[pts],True,col,1)
r=int(110/m);cv2.imwrite('rg_sat.jpg',cv2.resize(ov[cy-r:cy+r,cx-r:cx+r],(900,900)))
