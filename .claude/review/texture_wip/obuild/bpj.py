import json,numpy as np,sys
sys.path.insert(0,'.')
from cam import R
C=json.load(open('r2/camL.json'));p=C['p']
def bp(u,v,z):
    M=R(*p[3:6]);fo=p[6];d=np.array([(u-p[7])/fo,-(v-p[8])/fo,1.0]);w=M.T@d;Cc=np.array(p[:3])
    t=(z-Cc[2])/w[2];return Cc+t*w
if __name__=='__main__':
    for a in sys.argv[1:]:
        u,v,z=map(float,a.split(','));print(a,np.round(bp(u,v,z),2))
