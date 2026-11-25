# Heights from shadows in the 23 Mar 2000 aerial. Sun from the light-tower head shadow: az 49.2, elev 39.4.
import cv2,numpy as np,json,sys
M=0.3019; C=json.load(open('centres_fix.json'))
import os
f=os.environ.get('F','ge_2000-03-23_r950.jpg'); cx,cy=C[f]
g=cv2.GaussianBlur(cv2.cvtColor(cv2.imread(f),cv2.COLOR_BGR2GRAY).astype(float),(5,5),1.2)
def prof(b,r0,r1,dr=0.2):
    rr=np.arange(r0,r1,dr); B=np.radians(b)
    X=(cx+rr*np.sin(B)/M).astype(np.float32); Y=(cy-rr*np.cos(B)/M).astype(np.float32)
    return rr,cv2.remap(g.astype(np.float32),X[None],Y[None],cv2.INTER_LINEAR)[0]
def step(b,r0,r1,sign,w=1.0):
    rr,v=prof(b,r0,r1); k=int(w/0.2)
    d=np.array([v[i+k:i+2*k].mean()-v[i-k:i].mean() if i>=k and i+2*k<=len(v) else 0 for i in range(len(v))])
    i=np.argmax(sign*d); return rr[i],sign*d[i]
if __name__=='__main__':
    b0,b1,ra,rb,sg=map(float,sys.argv[1:6])
    for b in np.arange(b0,b1+0.01,2.5):
        r,s=step(b,ra,rb,sg); print('%6.1f %6.1f %5.0f'%(b,r,s))
