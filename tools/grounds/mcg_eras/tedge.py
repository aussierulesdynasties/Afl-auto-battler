# Turf shadow edge: along each ray, first radius where brightness drops under thr and stays under it for `run` metres.
import os,sys,numpy as np
os.environ.setdefault('F','ge_2001-06-20_r950.jpg')
from shadow import prof
def tedge(b,r0,r1,thr,run=4.0):
    rr,v=prof(b,r0,r1); k=int(run/0.2); d=v<thr
    for i in range(len(v)-k):
        if d[i:i+k].all():
            # sub-sample: half-way crossing
            j=i; return rr[j]
    return np.nan
if __name__=='__main__':
    b0,b1,ra,rb,thr=map(float,sys.argv[1:6])
    _,v=prof(200,20,40); print('sunlit turf level ~%.0f'%np.median(v), file=sys.stderr)
    for b in np.arange(b0,b1+0.01,2.5): print('%.1f %.2f'%(b%360,tedge(b,ra,rb,thr)))
