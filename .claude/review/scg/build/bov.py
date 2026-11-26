# overlay every BLD block's eave rectangle (and ground footprint dotted) on the aerial photo, labelled
import sys,cv2,numpy as np,math
exec(open('meas.py').read());exec(open('blds.py').read())
x0,y0,x1,y1=map(int,sys.argv[1].split(','));out=sys.argv[2];k=float(sys.argv[3])
im=cv2.resize(cv2.imread('refs/scg.jpg')[y0:y1,x0:x1],None,fx=k,fy=k,interpolation=cv2.INTER_CUBIC)
def SS_(p):return (int((p[0]-x0)*k),int((p[1]-y0)*k))
cols=[(0,0,255),(0,255,255),(255,0,255),(0,255,0),(255,128,0),(255,255,255),(0,128,255),(128,0,255),(255,0,0),(0,0,0),(128,255,128)]
for i,b in enumerate(BLD):
    n,f,u0,u1,w0,w1,ze,rise,kind=b[:9];(ox,oy),a=FR[f];a=math.radians(a);U=np.array([math.cos(a),math.sin(a)]);W=np.array([-U[1],U[0]]);O=np.array([ox,oy])
    c=[O+u*U+w*W for u,w in ((u0,w0),(u1,w0),(u1,w1),(u0,w1))]
    for z,th in ((ze,2),):
        P=pr(np.array([[*p,z] for p in c]))
        for j in range(4):cv2.line(im,SS_(P[j]),SS_(P[(j+1)%4]),cols[i%len(cols)],th)
    if kind=='gable_w':r=[O+((u0+u1)/2)*U+w0*W,O+((u0+u1)/2)*U+w1*W]
    else:r=[O+u0*U+((w0+w1)/2)*W,O+u1*U+((w0+w1)/2)*W]
    RR_=pr(np.array([[*p,ze+rise] for p in r]));cv2.line(im,SS_(RR_[0]),SS_(RR_[1]),cols[i%len(cols)],1)
    m=pr(np.array([[*(sum(c)/4),ze+rise]]))[0];cv2.putText(im,n,SS_(m),0,0.6,cols[i%len(cols)],2)
for x in range(x0-x0%10+10,x1,10):
    X=int((x-x0)*k)
    if x%50==0:cv2.line(im,(X,0),(X,im.shape[0]),(255,255,0),1);cv2.putText(im,str(x),(X+2,14),0,0.45,(255,255,0),1)
for y in range(y0-y0%10+10,y1,10):
    Y=int((y-y0)*k)
    if y%50==0:cv2.line(im,(0,Y),(im.shape[1],Y),(255,255,0),1);cv2.putText(im,str(y),(2,Y-2),0,0.45,(255,255,0),1)
cv2.imwrite(out,im)
