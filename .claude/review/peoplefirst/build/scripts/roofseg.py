import cv2,numpy as np,json
S=json.load(open('sat.json'));m=S['mpp']
im=cv2.imread('sat.png');hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
w=((hsv[:,:,2]>185)&(hsv[:,:,1]<45)).astype(np.uint8)*255
w=cv2.morphologyEx(w,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(w)
sx,sy=int(S['px']+(-90)/m),int(S['py']-0/m)
L=lab[sy,sx];print('label',L,st[L])
mask=(lab==L).astype(np.uint8)*255
cv2.imwrite('roof_mask.png',mask)
ov=im.copy();ov[mask>0]=(0.5*ov[mask>0]+np.array([0,0,127])).astype(np.uint8)
cv2.imwrite('roof_ov.jpg',cv2.resize(ov[200:2100,150:2150],(950,950)))
