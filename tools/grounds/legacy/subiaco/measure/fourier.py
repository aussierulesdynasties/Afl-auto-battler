# fourier.py IN.json K [col] : robust polar Fourier fit r(a) of traced radii; prints rms and worst; writes IN_fit.json
import sys,json,numpy as np
d=json.load(open(sys.argv[1]));K=int(sys.argv[2]);col=int(sys.argv[3]) if len(sys.argv)>3 else 1
A=np.array([x[0] for x in d if x[col]]);R=np.array([x[col] for x in d if x[col]])
def basis(a):
    t=np.radians(a);return np.column_stack([np.ones_like(t)]+[f(k*t) for k in range(1,K+1) for f in (np.cos,np.sin)])
keep=np.ones(len(A),bool)
for it in range(8):
    c,*_=np.linalg.lstsq(basis(A[keep]),R[keep],rcond=None);res=R-basis(A)@c
    sig=1.4826*np.median(np.abs(res[keep]));keep=np.abs(res)<max(3*sig,0.3)
print('K',K,'kept',keep.sum(),'/',len(A),'rms %.2f m'%np.sqrt((res[keep]**2).mean()),'p95 %.2f'%np.percentile(np.abs(res[keep]),95))
json.dump({'K':K,'c':c.tolist(),'kept':int(keep.sum()),'n':len(A),'rms':float(np.sqrt((res[keep]**2).mean()))},open(sys.argv[1].replace('.json','_fit.json'),'w'))
