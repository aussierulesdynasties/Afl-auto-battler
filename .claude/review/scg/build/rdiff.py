import cv2,numpy as np,sys
x0,y0,x1,y1=190,390,490,615;k=3
a=cv2.imread('refs/scg.jpg')[y0:y1,x0:x1];b=cv2.imread('out/r0.png')[y0:y1,x0:x1]
def gm(im):
    h=cv2.cvtColor(im,cv2.COLOR_BGR2HSV);return ((h[...,0]>30)&(h[...,0]<90)&(h[...,1]>50)&(h[...,2]>45))
yy,xx=np.mgrid[y0:y1,x0:x1];keep=(xx<300+(yy-395)*(165/175)-6)
pa=gm(a)&keep;pb=gm(b)&keep
pa=cv2.morphologyEx(pa.astype(np.uint8),cv2.MORPH_OPEN,np.ones((2,2),np.uint8))>0
o=(a*0.55).astype(np.uint8)
o[pa&pb]=(60,160,60);o[pa&~pb]=(0,0,255);o[~pa&pb]=(255,120,0)
print('IoU',(pa&pb).sum()/max(1,(pa|pb).sum()),'photo-only',(pa&~pb).sum(),'model-only',(~pa&pb).sum())
o=cv2.resize(o,None,fx=k,fy=k,interpolation=cv2.INTER_NEAREST)
for x in range(200,490,50):X=(x-x0)*k;cv2.line(o,(X,0),(X,o.shape[0]),(255,255,0),1);cv2.putText(o,str(x),(X+2,14),0,0.45,(255,255,0),1)
for y in range(400,615,50):Y=(y-y0)*k;cv2.line(o,(0,Y),(o.shape[1],Y),(255,255,0),1);cv2.putText(o,str(y),(2,Y-2),0,0.45,(255,255,0),1)
cv2.imwrite(sys.argv[1] if len(sys.argv)>1 else 'g/rdiff.png',o)
