# satellite resampled into the top-down render's world grid (same scale, north up); writes sat | model | blend + outline
import json,math,numpy as np,cv2,sys
J=json.load(open('sat/sat.json'));M=np.array(J['M']);t=np.array(J['t']);Mi=np.linalg.inv(M);z=J['z'];n=2**z
sat=cv2.imread('sat/sat.png');top=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED);out=sys.argv[2]
N=top.shape[0];PCx,PCy=0.94,-11.82;H=170.0
jj,ii=np.meshgrid(np.arange(N),np.arange(N))
X=PCx-H+(jj+0.5)*(2*H/N);Y=PCy+H-(ii+0.5)*(2*H/N)
lo=Mi[0,0]*(X-t[0])+Mi[0,1]*(Y-t[1]);la=Mi[1,0]*(X-t[0])+Mi[1,1]*(Y-t[1])
tx=(lo+180)/360*n;ty=(1-np.arcsinh(np.tan(np.radians(la)))/math.pi)/2*n
mx=((tx-J['x0'])*256).astype(np.float32);my=((ty-J['y0'])*256).astype(np.float32)
S_=cv2.remap(sat,mx,my,cv2.INTER_CUBIC);cv2.imwrite('sat/sat_world.png',S_)
al=top[:,:,3:4]/255.0;mod=top[:,:,:3]
bl=(S_*(1-0.5*al)+mod*0.5*al).astype(np.uint8)
edge=cv2.Canny((top[:,:,3]>10).astype(np.uint8)*255,50,150);ol=S_.copy();ol[edge>0]=(0,0,255)
for k in range(-150,151,50):   # 50 m grid
    p=int((k+H)/(2*H)*N);cv2.line(ol,(p,0),(p,N),(255,255,0),1);cv2.line(ol,(0,p),(N,p),(255,255,0),1)
cv2.imwrite(out+'_blend.png',bl);cv2.imwrite(out+'_outline.png',ol)
cv2.imwrite(out+'_trio.png',np.hstack([cv2.resize(x,(850,850)) for x in (S_,np.where(al>0,mod,40).astype(np.uint8),bl)]))
