import numpy as np,json,cv2,sys
from PIL import Image
A=np.asarray(Image.open('lplan_all_clean.png').convert('RGB')).astype(np.uint8)
s0,t1,M=-200,200,0.25
hsv=cv2.cvtColor(A,cv2.COLOR_RGB2HSV)
white=((hsv[...,2]>175)&(hsv[...,1]<45)).astype(np.uint8)
K=int(sys.argv[1]) if len(sys.argv)>1 else 15
m=cv2.morphologyEx(white,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(K,K)))
n,lab,st,_=cv2.connectedComponentsWithStats(m)
labs=set(lab[y,x] for x,y in [(400,800),(1200,800),(800,330),(800,1260)]);labs.discard(0);print(labs)
R=np.isin(lab,list(labs)).astype(np.uint8)
op=np.zeros_like(R);cv2.rectangle(op,(560,400),(1060,1150),1,-1)
S=cv2.morphologyEx(R|op,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(25,25)))
cs,_=cv2.findContours(S,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);C=max(cs,key=cv2.contourArea)[:,0]
pts=[(s0+y*M,t1-x*M) for x,y in C];json.dump(pts,open('roof_outline2.json','w'))
o=A.copy();cv2.drawContours(o,[C[:,None]],-1,(255,0,255),2);Image.fromarray(o).resize((1000,1000)).save('roof_outline2.jpg',quality=88)
