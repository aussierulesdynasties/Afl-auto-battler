import cv2,numpy as np,json
S=json.load(open('sat.json'));m=S['mpp'];im=cv2.imread('sat.png')
N=2048;HALF=200.0;ppm=N/(2*HALF)
xs=(np.arange(N)+0.5)/ppm-HALF;X,Y=np.meshgrid(xs,-xs)  # row 0 = north
mx=(S['px']+X/m).astype(np.float32);my=(S['py']-Y/m).astype(np.float32)
sat=cv2.remap(im,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);cv2.imwrite('g_sat.png',sat)
lab=cv2.cvtColor(cv2.GaussianBlur(sat,(5,5),0),cv2.COLOR_BGR2LAB).reshape(-1,3).astype(np.float32)
K=12;_,lb,C=cv2.kmeans(lab,K,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,30,0.5),3,cv2.KMEANS_PP_CENTERS)
lb=lb.reshape(N,N);np.save('g_km.npy',lb)
Cb=cv2.cvtColor(C.reshape(1,K,3).astype(np.uint8),cv2.COLOR_LAB2BGR)[0]
pal=np.array([[255,0,0],[0,255,0],[0,0,255],[255,255,0],[255,0,255],[0,255,255],[128,0,0],[0,128,0],[0,0,128],[128,128,0],[128,0,128],[0,128,128]],np.uint8)
vis=pal[lb];sw=np.zeros((K*40,300,3),np.uint8)
for k in range(K):sw[k*40:(k+1)*40,:150]=pal[k];sw[k*40:(k+1)*40,150:]=Cb[k];cv2.putText(sw,str(k),(5,28),0,0.8,(255,255,255),2)
cv2.imwrite('g_km.jpg',cv2.resize(np.hstack([cv2.resize(sat,(1024,1024)),cv2.resize(vis,(1024,1024),interpolation=cv2.INTER_NEAREST)]),(2048,1024)));cv2.imwrite('g_sw.png',sw)
print([(k,Cb[k].tolist(),int((lb==k).sum())) for k in range(K)])
