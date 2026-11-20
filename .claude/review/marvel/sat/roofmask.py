# Roof outline from the clean plan: bright low-saturation pixels, largest blob around the field, fill, contour.
import numpy as np,json,cv2
from PIL import Image
A=np.asarray(Image.open('lplan_all_clean.png').convert('RGB')).astype(np.uint8)
s0,t1,M=-200,200,0.25
hsv=cv2.cvtColor(A,cv2.COLOR_RGB2HSV)
white=((hsv[...,2]>185)&(hsv[...,1]<40)).astype(np.uint8)
# field (green) inside
green=((hsv[...,0]>30)&(hsv[...,0]<90)&(hsv[...,1]>60)).astype(np.uint8)
k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9))
m=cv2.morphologyEx(white|0,cv2.MORPH_CLOSE,k)
n,lab,st,_=cv2.connectedComponentsWithStats(m)
c=lab[800,400+0]  # pixel at s=0,t=100 (west roof)
print('label at west roof',c,st[c])
R=(lab==c).astype(np.uint8)
# add opening (the field and its dark surround) to make a solid disc
op=np.zeros_like(R);cv2.rectangle(op,(560,400),(1060,1150),1,-1)
S=cv2.morphologyEx(R|op,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(25,25)))
S=nd.binary_fill_holes(S).astype(np.uint8) if False else S
cs,_=cv2.findContours(S,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);C=max(cs,key=cv2.contourArea)[:,0]
pts=[(s0+y*M,t1-x*M) for x,y in C]
json.dump(pts,open('roof_outline_raw.json','w'))
o=A.copy();cv2.drawContours(o,[C[:,None]],-1,(255,0,255),2);Image.fromarray(o).save('roof_outline.jpg',quality=88)
P=np.array(pts);print('s range',P[:,0].min(),P[:,0].max(),'t range',P[:,1].min(),P[:,1].max(),len(P))
