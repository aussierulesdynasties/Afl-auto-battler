# fit a 3x4 colour transform taking photo B's colours to the reference photo's, from model faces both photos see
exec(open('geo.py').read())
import cv2,sys
def camuv(cj):
    q=json.load(open(cj))['p'];Mc=R(*q[3:6]);d=(np.array(V,float)-np.array(q[:3]))@Mc.T
    return np.stack([q[7]+q[6]*d[:,0]/d[:,2],q[8]-q[6]*d[:,1]/d[:,2]],1),d[:,2]
A,zA=camuv('cam.json');B,zB=camuv(sys.argv[1])
ia=cv2.imread('refs/scg.jpg');ib=cv2.imread(sys.argv[2])
lo,hi=float(sys.argv[3]),float(sys.argv[4])
xa=[];xb=[]
for idx,m in F:
    if m in('tower','lamp','headback','grass','seat'):continue
    c=np.array(V)[list(idx)].mean(0);ang=math.degrees(math.atan2(c[1]-PC[1],c[0]-PC[0]))%360
    if not lo<=ang<=hi:continue
    ua=A[list(idx)].mean(0);ub=B[list(idx)].mean(0)
    if not(0<=ua[0]<ia.shape[1]-3 and 0<=ua[1]<ia.shape[0]-3 and 0<=ub[0]<ib.shape[1]-6 and 0<=ub[1]<ib.shape[0]-6):continue
    pa=ia[int(ua[1])-1:int(ua[1])+2,int(ua[0])-1:int(ua[0])+2].reshape(-1,3).mean(0)
    k=3;pb=ib[int(ub[1])-k:int(ub[1])+k+1,int(ub[0])-k:int(ub[0])+k+1].reshape(-1,3).mean(0)
    xa.append(pa);xb.append(pb)
xa=np.array(xa);xb=np.array(xb);M=np.zeros((4,3))
# per channel: match the quantiles of the shared region (robust to misregistered samples), gain+offset only
for ch in range(3):
    qa=np.percentile(xa[:,ch],np.arange(10,91,5));qb=np.percentile(xb[:,ch],np.arange(10,91,5))
    g,o=np.polyfit(qb,qa,1);M[ch,ch]=g;M[3,ch]=o
print('pairs',len(xa),'gain/offset',np.round(np.diag(M[:3]),2),np.round(M[3],1))
np.save(sys.argv[5],M)
