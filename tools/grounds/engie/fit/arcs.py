import os
import numpy as np, json, math
from scipy.optimize import least_squares
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'composite.py')).read().split('OUT={}')[0])
def circ_res(Q,c,R): return np.hypot(Q[:,0]-c[0],Q[:,1]-c[1])-R
RES={}
for key,d in (('rf',dF),('rb',dB)):
    for nm,st in STANDS.items():
        b,P=pts(key); m=inr(b,*st['fit']); Q=P[m]
        # free circle
        def f1(x): return circ_res(Q,x[:2],x[2])
        x=least_squares(f1,[0,0,120],loss='soft_l1',f_scale=1).x; r=f1(x); k=np.abs(r)<4; x=least_squares(lambda y:circ_res(Q[k],y[:2],y[2]),x).x; r=circ_res(Q,x[:2],x[2]); k=np.abs(r)<4
        free=np.sqrt((r[k]**2).mean())
        # tangent circle: centre on the inward normal of the bowl offset at bj, radius R
        def tcirc(bj,R):
            t=tparam_at_bearing(bj,d); P0,tg=offset_pt(np.array([t]),d); n=np.array([tg[0][1],-tg[0][0]])  # inward
            return P0[0]+R*n, R
        def f2(y):
            c,R=tcirc(y[0],y[1]); rr=circ_res(Q,c,R); return np.clip(rr,-4,4)
        best=None
        for bj0 in np.arange(*st['search'],3.0):
            for R0 in (100,150,250,400):
                try: z=least_squares(f2,[bj0,R0],bounds=([st['search'][0],40],[st['search'][1],3000]))
                except Exception: continue
                if best is None or z.cost<best.cost: best=z
        c,R=tcirc(*best.x); rr=circ_res(Q,c,R); kk=np.abs(rr)<4
        print('%s %s  free arc R=%.0f rms %.2f (n %d) | tangent-joined arc at %.1f deg R=%.0f rms %.2f 95%% %.2f max %.2f (n %d, %d mistraces >4 m)'%(key,nm,x[2],free,k.sum(),best.x[0],R,np.sqrt((rr[kk]**2).mean()),np.percentile(np.abs(rr[kk]),95),np.abs(rr[kk]).max(),kk.sum(),(~kk).sum()))
        RES['%s_%s'%(key,nm)]={'bj':float(best.x[0]),'c':c.tolist(),'R':float(R),'free':x.tolist()}
json.dump(RES,open('arcs.json','w'))
