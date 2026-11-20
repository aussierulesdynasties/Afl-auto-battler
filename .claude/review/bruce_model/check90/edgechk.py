# for each model ring and bearing: offset (m) to the strongest colour edge in the 1990 photo within +-4 m along the ray
import sys,json,numpy as np,cv2
sys.path.insert(0,'C:/kt/bruce1990/.claude/review/bruce_model');import aerial90 as A
P=json.load(open('C:/kt/bruce1990/.claude/review/bruce_model/parts.json'));TH=np.array(P['ring_th'])
lab=cv2.cvtColor(cv2.GaussianBlur(cv2.imread('bruce/legacy/src90.png'),(0,0),1.5),cv2.COLOR_BGR2LAB).astype(np.float32)
D=np.arange(-4,4.01,0.125);out={}
bd=(np.degrees(TH)+180)%360-180;sec=A.sector(bd)
for k in ('fence','toe','top_in','top_out','foot'):
    R=np.array(P['rings'][k]);r=np.hypot(R[:,0]-A.CX,R[:,1]-A.CY);z=R[:,2]
    off=[]
    for i,t in enumerate(TH):
        rr=r[i]+D;Q=np.c_[A.CX+rr*np.cos(t),A.CY+rr*np.sin(t)];px=A.m2px(Q,z[i]).astype(np.float32)
        s=cv2.remap(lab,px[:,0:1],px[:,1:2],cv2.INTER_LINEAR)[:,0];g=np.linalg.norm(np.diff(s,axis=0),axis=1)
        off.append(D[:-1][np.argmax(g)]+0.0625)
    out[k]=np.array(off)
print('ring      '+' '.join('%8s'%s for s in ('N','E','SE','S','SW','all')))
for k,o in out.items():
    print('%-9s'%k+' '.join('%8.2f'%np.median(np.abs(o[sec==s])) for s in ('N','E','SE','S','SW'))+' %8.2f'%np.median(np.abs(o)),' 90%%: %.2f'%np.percentile(np.abs(o),90))
print('signed (photo edge beyond model +)')
for k,o in out.items():
    print('%-9s'%k+' '.join('%8.2f'%np.median(o[sec==s]) for s in ('N','E','SE','S','SW')))
np.save('edgeoff.npy',np.array([out[k] for k in out]))
