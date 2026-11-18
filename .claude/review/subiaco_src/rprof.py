import sys,numpy as np
from PIL import Image
I=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(float)
L=I.mean(2)
p0=np.array([697.,182.]);p1=np.array([865.,320.]);u=(p1-p0)/np.linalg.norm(p1-p0);n=np.array([u[1],-u[0]])
def s(p):
    x,y=p;x0,y0=int(x),int(y);fx,fy=x-x0,y-y0
    return L[y0,x0]*(1-fx)*(1-fy)+L[y0,x0+1]*fx*(1-fy)+L[y0+1,x0]*(1-fx)*fy+L[y0+1,x0+1]*fx*fy
for t in range(-10,240,10):
    q=p0+u*t;row=''
    for o in np.arange(-45,20,1.0):
        v=s(q+n*o);row+=' .:-=+*#%@'[min(9,int(v/26))]
    print('%4d (%5.1f,%5.1f) %s'%(t,q[0],q[1],row))
