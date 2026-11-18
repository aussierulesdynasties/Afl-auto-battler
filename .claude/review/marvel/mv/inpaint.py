import cv2,numpy as np
im=cv2.imread('mu_full.png');hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
H,S,V=[hsv[...,i].astype(int) for i in range(3)]
teal=(H>=60)&(H<=105)&(S>=25)&(V>=40)
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(int);med=cv2.medianBlur(g.astype(np.uint8),41).astype(int)
dark=g<med-22
deck=np.zeros(g.shape,np.uint8)
cv2.fillPoly(deck,[np.int32(np.array([(310,393),(1473,382),(1580,493),(172,497)])*2)],1)   # near panel deck (mu px x2)
cv2.fillPoly(deck,[np.int32(np.array([(538,219),(1296,212),(1300,170),(1200,150),(880,130),(560,150),(535,175)])*2)],1)   # far panel deck
m=((teal|(dark&(deck>0)))).astype(np.uint8)*255;m[1400:]=0
m=cv2.dilate(m,np.ones((7,7),np.uint8))
out=cv2.inpaint(im,m,9,cv2.INPAINT_TELEA)
cv2.imwrite('mu_roof.png',out)
cv2.imwrite('ip_crop.png',np.hstack([im[350:1000,300:1500],out[350:1000,300:1500]])[::2,::2])
