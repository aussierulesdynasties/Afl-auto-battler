# Centre of a capture's arena, fitting the March 2000 ellipse (fixed shape) to sunlit edge points only.
import cv2,numpy as np,json,sys
from arena_edge import edge_points
from arena_fit import robust_ellipse,M
from scipy.optimize import least_squares
ref='ge_2000-03-23_r950.jpg'
P=edge_points(ref); e,_=robust_ellipse(P); A,B,ang=e['A'],e['B'],np.radians(e['ang'])
print('ref',{k:round(v,2) if isinstance(v,float) else v for k,v in e.items()})
def fit(f,b0,b1):
    Q=edge_points(f); bx=np.degrees(np.arctan2(Q[:,0]-e['cx'],-(Q[:,1]-e['cy'])))%360
    sel=((bx-b0)%360)<=((b1-b0)%360); Q=Q[sel]
    def res(p):
        x=Q[:,0]-p[0]; y=Q[:,1]-p[1]; ca,sa=np.cos(ang),np.sin(ang)
        u=(x*ca+y*sa)/(A/2); v=(-x*sa+y*ca)/(B/2); return (np.hypot(u,v)-1)*(A+B)/4
    p=least_squares(res,[e['cx'],e['cy']],loss='soft_l1',f_scale=3).x
    r=res(p); k=np.abs(r)<3*1.4826*np.median(np.abs(r)); p=least_squares(lambda q:res(q)[k],p).x; r=res(p)[k]
    return p,float(np.sqrt(np.mean(r**2))*M),int(k.sum()),len(Q)
if __name__=='__main__':
    C=json.load(open('centres.json'))
    for f in sys.argv[3:]:
        p,rms,k,n=fit(f,float(sys.argv[1]),float(sys.argv[2])); print(f,p.round(2),'rms m %.2f'%rms,k,'/',n)
        C[f]=[float(p[0]),float(p[1])]
    json.dump(C,open('centres_fix.json','w'),indent=0)
