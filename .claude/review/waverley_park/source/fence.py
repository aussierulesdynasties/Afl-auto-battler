exec(open('prof.py',encoding='utf-8').read().split("if __name__")[0])
from scipy.ndimage import gaussian_filter1d
# fence curve: polar-sorted outline resampled by arc length, smoothed
_t=np.radians(np.arange(-180,180,0.1));_r=np.interp(_t,_pa,_pr,period=2*math.pi)
Q=PC+np.c_[np.cos(_t),np.sin(_t)]*_r[:,None]
Q=np.c_[gaussian_filter1d(Q[:,0],15,mode='wrap'),gaussian_filter1d(Q[:,1],15,mode='wrap')]
seg=np.hypot(*np.diff(np.r_[Q,Q[:1]],axis=0).T);SL=np.r_[0,np.cumsum(seg)];PER=SL[-1]
def F(s):
    s=np.asarray(s,float)%PER;x=np.interp(s,SL,np.r_[Q[:,0],Q[0,0]]);y=np.interp(s,SL,np.r_[Q[:,1],Q[0,1]]);return np.c_[x,y]
def N(s):
    a=F(np.asarray(s)-0.5);b=F(np.asarray(s)+0.5);t=b-a;t/=np.linalg.norm(t,axis=1)[:,None];return np.c_[t[:,1],-t[:,0]]  # outward for ccw
def P(s,d,z):
    s=np.atleast_1d(s);xy=F(s)+N(s)*np.atleast_1d(d)[:,None] if np.ndim(d) else F(s)+N(s)*d
    return np.c_[xy,np.broadcast_to(z,len(s))]
def th_of_s(s):
    xy=F(s);return np.degrees(np.arctan2(xy[:,1]-PC[1],xy[:,0]-PC[0]))
def s_of_th(th):
    T=th_of_s(np.arange(0,PER,0.1));o=np.argsort(T);return np.interp(th,T[o],np.arange(0,PER,0.1)[o],period=360)
#MAIN
if __name__=='__main__':
    print('PER',PER,'s0 theta',th_of_s([0,PER/4]))
    # check outward
    print(np.linalg.norm(P([10],5,0)[0,:2]-PC)-np.linalg.norm(F([10])[0]-PC))
